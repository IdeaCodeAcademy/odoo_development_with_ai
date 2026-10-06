import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError

HEADER_SNAPSHOTS = ('quoted_currency_id', 'quoted_by_id', 'quoted_date', 'confirmed_currency_id', 'confirmed_by_id', 'confirmed_date', 'seller_name_snapshot',
                    'cancelled_by_id', 'cancelled_date', 'amount_total')
LINE_SNAPSHOTS = ('pricing_rule_id', 'price_per_kg', 'amount', 'hair_type_snapshot', 'grade_snapshot',
                  'length_snapshot', 'length_min_snapshot', 'length_max_snapshot', 'length_open_ended_snapshot')


class HairPurchase(models.Model):
    _inherit = 'hair.purchase'

    state = fields.Selection(selection_add=[('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
                             ondelete={'confirmed': 'set default', 'cancelled': 'set default'})
    quoted_currency_id = fields.Many2one('res.currency', readonly=True, copy=False, ondelete='restrict')
    quoted_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict', tracking=True)
    quoted_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    confirmed_currency_id = fields.Many2one('res.currency', readonly=True, copy=False, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', related=False, compute='_compute_currency_id')
    confirmed_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict', tracking=True)
    confirmed_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    seller_name_snapshot = fields.Char(readonly=True, copy=False)
    amount_total = fields.Monetary(compute='_compute_amount_total', store=True, currency_field='currency_id')
    cancellation_reason = fields.Text(copy=False, tracking=True)
    cancelled_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict', tracking=True)
    cancelled_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    @api.depends('confirmed_currency_id', 'quoted_currency_id', 'company_id.currency_id')
    def _compute_currency_id(self):
        for purchase in self:
            purchase.currency_id = purchase.confirmed_currency_id or purchase.quoted_currency_id or purchase.company_id.currency_id

    @api.depends('line_ids.amount', 'currency_id')
    def _compute_amount_total(self):
        for purchase in self:
            purchase.amount_total = purchase.currency_id.round(math.fsum(purchase.line_ids.mapped('amount')))

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in (*HEADER_SNAPSHOTS, 'cancellation_reason'):
            if name in field_list:
                values[name] = False
        return values

    def _check_derived_values(self, vals):
        super()._check_derived_values(vals)
        if 'cancellation_reason' in vals:
            self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        if set(HEADER_SNAPSHOTS) & vals.keys():
            raise ValidationError(self.env._('Commercial snapshots and totals can only be set by workflow actions.'))

    def write(self, vals):
        if 'cancellation_reason' in vals:
            self._require_hair_role('hair_supplier.hair_supplier_group_manager')
            self._lock_quality_records()
            if any(purchase.state not in ('draft', 'inspection', 'confirmed') for purchase in self):
                raise ValidationError(self.env._('Cancellation reasons cannot change on terminal purchases.'))
        return super().write(vals)

    def _validated_quotes(self):
        if self.state != 'inspection' or not self.quality_approved:
            raise ValidationError(self.env._('Quality must be approved before commercial pricing or confirmation.'))
        if not self.line_ids or any(not line.grade_id or not line.hair_type_id or not line.length_id or line.payable_weight <= 0 for line in self.line_ids):
            raise ValidationError(self.env._('Pricing requires complete classification, approved grades and positive payable kg.'))
        quotes = [(line, self.env['hair.pricing.rule']._quote(
            self.company_id, line.hair_type_id, line.grade_id, line.length_id, self.date, line.payable_weight,
        )) for line in self.line_ids]
        if any(not math.isfinite(quote['amount']) or quote['amount'] < 0 for _line, quote in quotes):
            raise ValidationError(self.env._('Purchase amounts must be finite and nonnegative.'))
        return quotes

    def _confirmation_quotes(self):
        return self._validated_quotes()

    def action_quote_purchase(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self._lock_quality_records()
        quotes = self._validated_quotes()
        self._write_workflow({'quoted_currency_id': self.company_id.currency_id.id})
        for line, quote in quotes:
            line._write_quality({
                'pricing_rule_id': quote['rule_id'], 'price_per_kg': quote['price_per_kg'], 'amount': quote['amount'],
                'hair_type_snapshot': line.hair_type_id.display_name, 'grade_snapshot': line.grade_id.display_name,
                'length_snapshot': line.length_id.display_name, 'length_min_snapshot': line.length_id.length_min,
                'length_max_snapshot': line.length_id.length_max, 'length_open_ended_snapshot': line.length_id.open_ended,
            })
        self._write_workflow({'quoted_by_id': self.env.user.id, 'quoted_date': fields.Datetime.now()})
        self.message_post(body=self.env._('Price computed for review: %(amount)s %(currency)s.',
                                         amount=self.amount_total, currency=self.currency_id.name))
        return True

    def action_confirm_purchase(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self._lock_quality_records()
        if self.state == 'confirmed':
            return True
        quotes = self._confirmation_quotes()
        if not self.quoted_date or self.quoted_currency_id != self.company_id.currency_id:
            raise ValidationError(self.env._('Compute and review pricing before confirmation.'))
        for line, quote in quotes:
            if (line.pricing_rule_id.id != quote['rule_id'] or line.price_per_kg != quote['price_per_kg']
                    or line.amount != quote['amount'] or line.hair_type_snapshot != line.hair_type_id.display_name
                    or line.grade_snapshot != line.grade_id.display_name or line.length_snapshot != line.length_id.display_name
                    or line.length_min_snapshot != line.length_id.length_min or line.length_max_snapshot != line.length_id.length_max
                    or line.length_open_ended_snapshot != line.length_id.open_ended):
                raise ValidationError(self.env._('Pricing or classification changed; recompute and review the quote before confirming.'))
        self._write_workflow({'confirmed_currency_id': self.quoted_currency_id.id, 'state': 'confirmed',
                              'confirmed_by_id': self.env.user.id, 'confirmed_date': fields.Datetime.now(),
                              'seller_name_snapshot': self.seller_id.name})
        self.message_post(body=self.env._('Commercial purchase confirmed: %(amount)s %(currency)s.',
                                         amount=self.amount_total, currency=self.currency_id.name))
        return True

    def action_return_to_draft(self):
        result = super().action_return_to_draft()
        self._write_workflow({'quoted_currency_id': False, 'quoted_by_id': False, 'quoted_date': False})
        return result

    def action_cancel_purchase(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self._lock_quality_records()
        if self.state == 'cancelled':
            return True
        if self.state not in ('draft', 'inspection', 'confirmed'):
            raise ValidationError(self.env._('Only draft, inspected or confirmed purchases can be cancelled.'))
        if not self.cancellation_reason or not self.cancellation_reason.strip():
            raise ValidationError(self.env._('A cancellation reason is required.'))
        # No payment/receipt integration exists yet. Future paid/received states
        # must use a defined reversal workflow rather than this cancellation path.
        self._write_workflow({'state': 'cancelled', 'cancelled_by_id': self.env.user.id,
                              'cancelled_date': fields.Datetime.now()})
        return True


class HairPurchaseLine(models.Model):
    _inherit = 'hair.purchase.line'

    currency_id = fields.Many2one(related='purchase_id.currency_id')
    pricing_rule_id = fields.Many2one('hair.pricing.rule', readonly=True, copy=False, check_company=True, ondelete='restrict')
    price_per_kg = fields.Float(readonly=True, copy=False, digits=0)
    amount = fields.Monetary(readonly=True, copy=False, currency_field='currency_id')
    hair_type_snapshot = fields.Char(readonly=True, copy=False)
    grade_snapshot = fields.Char(readonly=True, copy=False)
    length_snapshot = fields.Char(readonly=True, copy=False)
    length_min_snapshot = fields.Float(readonly=True, copy=False)
    length_max_snapshot = fields.Float(readonly=True, copy=False)
    length_open_ended_snapshot = fields.Boolean(readonly=True, copy=False)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in LINE_SNAPSHOTS:
            if name in field_list:
                values[name] = False
        return values

    def _check_weight_values(self, vals):
        super()._check_weight_values(vals)
        if set(LINE_SNAPSHOTS) & vals.keys():
            raise ValidationError(self.env._('Pricing and classification snapshots cannot be entered manually.'))

    def _write_quality(self, vals):
        if 'grade_id' in vals and not vals['grade_id']:
            vals = {**vals, **dict.fromkeys(LINE_SNAPSHOTS, False)}
        return super()._write_quality(vals)
