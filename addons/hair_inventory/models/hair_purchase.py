from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HairPurchase(models.Model):
    _inherit = 'hair.purchase'

    state = fields.Selection(selection_add=[('received', 'Received')], ondelete={'received': 'set default'})

    last_receipt_date = fields.Datetime(readonly=True, copy=False)
    last_receipt_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict')

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        values.update(dict.fromkeys(set(field_list) & {'last_receipt_date', 'last_receipt_by_id'}, False))
        return values

    def _check_derived_values(self, vals):
        super()._check_derived_values(vals)
        if {'last_receipt_date', 'last_receipt_by_id'} & vals.keys():
            raise ValidationError(self.env._('Receipt provenance can only be set by receiving stock.'))

    def action_confirm_purchase(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self._lock_quality_records()
        if self.state == 'received':
            return True
        return super().action_confirm_purchase()


class HairPurchaseLine(models.Model):
    _inherit = 'hair.purchase.line'

    receipt_line_ids = fields.One2many('hair.receipt.line', 'purchase_line_id')
    received_weight = fields.Float(compute='_compute_received_weight', digits=(16, 3), compute_sudo=False)

    @api.depends('purchase_id.name', 'hair_type_snapshot', 'length_snapshot', 'hair_type_id.name', 'length_id.name')
    def _compute_display_name(self):
        for line in self:
            line.display_name = f'{line.purchase_id.name}: {line.hair_type_snapshot or line.hair_type_id.display_name} / {line.length_snapshot or line.length_id.display_name} (#{line.id})'

    @api.depends('receipt_line_ids.quantity', 'receipt_line_ids.receipt_id.state')
    def _compute_received_weight(self):
        rows = self.env['hair.receipt.line']._read_group(
            [('purchase_line_id', 'in', self.ids), ('receipt_id.state', '=', 'done')],
            ['purchase_line_id'], ['quantity:sum'],
        )
        totals = {line.id: quantity for line, quantity in rows}
        for line in self:
            line.received_weight = totals.get(line.id, 0)
