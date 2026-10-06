from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class HairPurchase(models.Model):
    _inherit = 'hair.purchase'

    state = fields.Selection(selection_add=[('inspection', 'Inspection'), ('rejected', 'Rejected')],
                             ondelete={'inspection': 'set default', 'rejected': 'set default'}, tracking=True)
    quality_approved = fields.Boolean(readonly=True, copy=False, tracking=True)
    inspector_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict', tracking=True)
    inspection_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    inspection_notes = fields.Text(copy=False, tracking=True)
    rejection_reason = fields.Text(copy=False, tracking=True)
    revision_reason = fields.Text('Reason for Returning to Draft', copy=False, tracking=True)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in ('quality_approved', 'inspector_id', 'inspection_date', 'inspection_notes', 'rejection_reason'):
            if name in field_list:
                values[name] = False
        if 'state' in field_list:
            values['state'] = 'draft'
        return values

    def _check_derived_values(self, vals):
        super()._check_derived_values(vals)
        if {'quality_approved', 'inspector_id', 'inspection_date'} & vals.keys():
            raise ValidationError(self.env._('Inspection approval and provenance can only be set by workflow actions.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if {'inspection_notes', 'rejection_reason'} & vals.keys():
                raise ValidationError(self.env._('Record inspection findings after submitting the intake.'))
        return super().create(vals_list)

    def write(self, vals):
        self._lock_quality_records()
        intake_fields = {'date', 'company_id', 'seller_id', 'buyer_id', 'line_ids'}
        if intake_fields & vals.keys():
            self._require_hair_role('hair_supplier.hair_supplier_group_buyer')
            if any(purchase.state != 'draft' for purchase in self):
                raise ValidationError(self.env._('Return the intake to draft before changing its details.'))
        if 'revision_reason' in vals:
            self._require_hair_role('hair_supplier.hair_supplier_group_buyer')
            if any(purchase.state != 'inspection' for purchase in self):
                raise ValidationError(self.env._('Return-to-draft reasons apply only to submitted intakes.'))
        if {'inspection_notes', 'rejection_reason'} & vals.keys():
            self._require_hair_role('hair_purchase.hair_purchase_group_quality')
            if any(purchase.state != 'inspection' or purchase.quality_approved for purchase in self):
                raise ValidationError(self.env._('Inspection findings are editable only during an unapproved inspection.'))
        return super().write(vals)

    def _lock_quality_records(self):
        self.check_access('write')
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()

    def _require_hair_role(self, xml_id):
        if not self.env.su and not self.env.user.has_group(xml_id):
            raise AccessError(self.env._('You are not authorized for this hair workflow action.'))

    def action_submit_inspection(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_buyer')
        self._lock_quality_records()
        if self.state == 'inspection':
            return True
        if self.state != 'draft':
            raise ValidationError(self.env._('Only draft intakes can be submitted for inspection.'))
        if not self.line_ids or any(not line.hair_type_id or not line.length_id or line.payable_weight <= 0 for line in self.line_ids):
            raise ValidationError(self.env._('Every intake requires hair type, length and positive payable kg before inspection.'))
        self._write_workflow({'state': 'inspection'})
        return True

    def action_approve_quality(self):
        self.ensure_one()
        self._require_hair_role('hair_purchase.hair_purchase_group_quality')
        self._lock_quality_records()
        if self.state != 'inspection':
            raise ValidationError(self.env._('Only submitted intakes can be inspected.'))
        if self.quality_approved:
            return True
        if not self.line_ids or any(not line.proposed_grade_id for line in self.line_ids):
            raise ValidationError(self.env._('Assign a grade to every hair line before approving quality.'))
        for line in self.line_ids:
            line._write_quality({'grade_id': line.proposed_grade_id.id})
        self._write_workflow({'quality_approved': True, 'inspector_id': self.env.user.id,
                              'inspection_date': fields.Datetime.now()})
        grades = ', '.join(f'{line.id}: {line.grade_id.display_name}' for line in self.line_ids)
        self.message_post(body=self.env._('Quality approved. Line grades: %s', grades))
        return True

    def action_reject_quality(self):
        self.ensure_one()
        self._require_hair_role('hair_purchase.hair_purchase_group_quality')
        self._lock_quality_records()
        if self.state != 'inspection' or self.quality_approved:
            raise ValidationError(self.env._('Only an unapproved inspection can be rejected.'))
        if not self.rejection_reason or not self.rejection_reason.strip():
            raise ValidationError(self.env._('A rejection reason is required.'))
        self._write_workflow({'state': 'rejected', 'inspector_id': self.env.user.id,
                              'inspection_date': fields.Datetime.now()})
        return True

    def action_return_to_draft(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_buyer')
        self._lock_quality_records()
        if self.state != 'inspection':
            raise ValidationError(self.env._('Only intakes under inspection can return to draft.'))
        if self.quality_approved and (not self.revision_reason or not self.revision_reason.strip()):
            raise ValidationError(self.env._('A reason is required to reopen an approved inspection.'))
        grades = ', '.join(f'{line.id}: {line.grade_id.display_name}' for line in self.line_ids if line.grade_id)
        self.message_post(body=self.env._('Returned to draft. Previous approved grades: %(grades)s. Reason: %(reason)s',
                                         grades=grades, reason=self.revision_reason or self.env._('Correction before approval')))
        for line in self.line_ids:
            line._write_quality({'grade_id': False, 'proposed_grade_id': False})
        self._write_workflow({'state': 'draft', 'quality_approved': False, 'inspector_id': False,
                              'inspection_date': False, 'rejection_reason': False, 'revision_reason': False})
        return True


class HairPurchaseLine(models.Model):
    _inherit = 'hair.purchase.line'

    proposed_grade_id = fields.Many2one('hair.grade', string='Inspection Grade', check_company=True, ondelete='restrict', copy=False)
    grade_id = fields.Many2one('hair.grade', string='Approved Grade', check_company=True, ondelete='restrict', readonly=True, copy=False)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in ('grade_id', 'proposed_grade_id'):
            if name in field_list:
                values[name] = False
        return values

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if {'grade_id', 'proposed_grade_id'} & vals.keys():
                raise ValidationError(self.env._('Grades are assigned during inspection, not intake creation.'))
            self._require_draft_purchase(vals.get('purchase_id', self.env.context.get('default_purchase_id')))
        return super().create(vals_list)

    def write(self, vals):
        purchases = self.purchase_id
        if vals.get('purchase_id'):
            purchases |= self.env['hair.purchase'].browse(vals['purchase_id'])
        purchases._lock_quality_records()
        if 'grade_id' in vals:
            raise ValidationError(self.env._('Approved grades can only be set by quality approval.'))
        if 'proposed_grade_id' in vals:
            purchases._require_hair_role('hair_purchase.hair_purchase_group_quality')
            if any(purchase.state != 'inspection' or purchase.quality_approved for purchase in purchases):
                raise ValidationError(self.env._('Grades are editable only during an unapproved inspection.'))
        if vals.keys() - {'proposed_grade_id'}:
            for purchase in purchases:
                self._require_draft_purchase(purchase.id)
        return super().write(vals)

    def unlink(self):
        for purchase in self.purchase_id:
            self._require_draft_purchase(purchase.id)
        return super().unlink()

    def _require_draft_purchase(self, purchase_id):
        if purchase_id:
            purchase = self.env['hair.purchase'].browse(purchase_id)
            purchase._require_hair_role('hair_supplier.hair_supplier_group_buyer')
            purchase._lock_quality_records()
            if purchase.state != 'draft':
                raise ValidationError(self.env._('Hair lines can only be changed in draft intakes.'))
