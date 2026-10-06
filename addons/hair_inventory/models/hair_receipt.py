import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.float_utils import float_compare


class HairReceipt(models.Model):
    _name = 'hair.receipt'
    _description = 'Hair Partial Stock Receipt'
    _rec_name = 'purchase_id'
    _check_company_auto = True

    purchase_id = fields.Many2one('hair.purchase', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='purchase_id.company_id', store=True, index=True)
    picking_type_id = fields.Many2one('stock.picking.type', required=True, check_company=True, ondelete='restrict')
    line_ids = fields.One2many('hair.receipt.line', 'receipt_id', copy=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Received')], default='draft', readonly=True, required=True, copy=False)
    picking_id = fields.Many2one('stock.picking', readonly=True, copy=False, ondelete='restrict')
    received_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict')
    received_date = fields.Datetime(readonly=True, copy=False)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in ('state', 'picking_id', 'received_by_id', 'received_date', 'company_id'):
            if name in field_list:
                values[name] = 'draft' if name == 'state' else False
        return values

    def _require_warehouse(self):
        if not self.env.su and not self.env.user.has_group('hair_inventory.group_hair_warehouse'):
            raise AccessError(self.env._('Only hair warehouse users can receive purchases.'))

    def _check_paid(self):
        for receipt in self:
            purchase = receipt.purchase_id
            purchase._lock_quality_records()
            if (purchase.state not in ('paid', 'received') or purchase.payment_status != 'paid'
                    or not purchase.confirmed_date or not purchase.currency_id.is_zero(purchase.balance_amount)):
                raise ValidationError(self.env._('Hair receipts require a confirmed, fully paid purchase.'))

    def _check_values(self, vals):
        if {'picking_id', 'received_by_id', 'received_date', 'company_id'} & vals.keys() or vals.get('state', 'draft') != 'draft':
            raise ValidationError(self.env._('Receipt provenance can only be set by receipt posting.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._require_warehouse()
        for vals in vals_list:
            self._check_values(vals)
            self.env['hair.purchase'].browse(vals.get('purchase_id', self.env.context.get('default_purchase_id')))._lock_quality_records()
        receipts = super().create(vals_list)
        receipts._check_paid()
        receipts._check_operation()
        return receipts

    def _lock_draft(self):
        self._require_warehouse()
        self.check_access('write')
        self.purchase_id._lock_quality_records()
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()
        if any(receipt.state != 'draft' for receipt in self):
            raise ValidationError(self.env._('Completed receipt records cannot be changed.'))

    def write(self, vals):
        self._lock_draft()
        self._check_values(vals)
        if 'purchase_id' in vals:
            raise ValidationError(self.env._('A receipt cannot be moved to another purchase.'))
        result = super().write(vals)
        self._check_operation()
        return result

    def unlink(self):
        self._lock_draft()
        return super().unlink()

    def _check_operation(self):
        for receipt in self:
            operation = receipt.picking_type_id
            operation.check_access('read')
            if (not operation.active or operation.code != 'incoming' or operation.company_id != receipt.company_id
                    or operation.default_location_src_id.usage != 'supplier'
                    or operation.default_location_dest_id.usage != 'internal'):
                raise ValidationError(self.env._('Select an active company receipt operation from supplier to internal stock.'))

    def action_receive(self):
        self.ensure_one()
        # UI defaults belong to draft entry, not trusted stock provenance.
        return self.with_context({key: value for key, value in self.env.context.items()
                                  if not key.startswith('default_')})._receive_stock()

    def _receive_stock(self):
        self.ensure_one()
        self._require_warehouse()
        self.check_access('write')
        self.purchase_id._lock_quality_records()
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()
        if self.state == 'done':
            return True
        self._check_paid()
        self._check_operation()
        if self.env['decimal.precision'].precision_get('Product Unit') < 3:
            raise ValidationError(self.env._('Stock Product Unit precision must be at least three decimals for 0.001 kg receipts.'))
        if not self.line_ids:
            raise ValidationError(self.env._('Add receipt quantities before receiving stock.'))
        self.line_ids._check_source()
        purchase = self.purchase_id
        purchase.line_ids.invalidate_recordset(['received_weight'])
        for line in self.line_ids:
            if float_compare(line.quantity + line.purchase_line_id.received_weight,
                             line.purchase_line_id.payable_weight, precision_digits=3) > 0:
                raise ValidationError(self.env._('Cumulative received kg cannot exceed purchased payable kg.'))
        operation = self.picking_type_id
        picking = self.env['stock.picking']._create_hair_receipt({
            'hair_receipt_id': self.id, 'picking_type_id': operation.id, 'company_id': self.company_id.id,
            'partner_id': purchase.seller_id.id, 'origin': purchase.name,
            'location_id': operation.default_location_src_id.id, 'location_dest_id': operation.default_location_dest_id.id,
        })
        for line in self.line_ids:
            previous = self.env['stock.move'].search([
                ('hair_receipt_line_id.purchase_line_id', '=', line.purchase_line_id.id), ('state', '=', 'done'),
            ], order='id', limit=1)
            product = previous.product_id or line.purchase_line_id.hair_type_id._inventory_product()
            if (not product.active or not product.is_storable or product.tracking != 'lot'
                    or product.uom_id != self.env.ref('uom.product_uom_kgm')
                    or (product.company_id and product.company_id != self.company_id)):
                raise ValidationError(self.env._('The original receipt product must remain an active, compatible lot-tracked kg product.'))
            lot = self.env['stock.lot']._create_hair_receipt({
                'name': f'{purchase.name}/R{self.id}/L{line.id}', 'product_id': product.id,
                'company_id': self.company_id.id, 'hair_receipt_line_id': line.id,
            })
            move = self.env['stock.move']._create_hair_receipt({
                'hair_receipt_line_id': line.id, 'product_id': product.id, 'product_uom_qty': line.quantity,
                'uom_id': product.uom_id.id, 'picking_id': picking.id, 'company_id': self.company_id.id,
                'location_id': picking.location_id.id, 'location_dest_id': picking.location_dest_id.id,
            })
            move._action_confirm(merge=False)
            # Incoming confirmation pre-fills details in Odoo 20. Replace those
            # draft details with the one exact source-lot quantity, not a second
            # detail that would double the receipt.
            move.move_line_ids.unlink()
            self.env['stock.move.line'].create({
                'move_id': move.id, 'picking_id': picking.id, 'product_id': product.id, 'lot_id': lot.id,
                'quantity': line.quantity, 'uom_id': product.uom_id.id,
                'location_id': picking.location_id.id, 'location_dest_id': picking.location_dest_id.id,
            })
            move.picked = True
        picking._action_done()
        if picking.state != 'done':
            raise ValidationError(self.env._('Stock receipt did not complete.'))
        # Private action helper retains ORM permissions; no raw SQL/context bypass.
        super().write({'state': 'done', 'picking_id': picking.id, 'received_by_id': self.env.user.id,
                       'received_date': fields.Datetime.now()})
        # Update the locked parent on every partial receipt as well. This makes
        # overlapping repeatable-read transactions retry instead of using an
        # earlier cumulative-quantity snapshot after the first receipt commits.
        values = {'last_receipt_date': self.received_date, 'last_receipt_by_id': self.env.user.id}
        if all(float_compare(line.received_weight, line.payable_weight, precision_digits=3) == 0 for line in purchase.line_ids):
            values['state'] = 'received'
        purchase._write_workflow(values)
        purchase.message_post(body=self.env._('Partial stock receipt %(receipt)s completed: %(kg)s kg.',
                                             receipt=picking.name, kg=math.fsum(self.line_ids.mapped('quantity'))))
        return True


class HairReceiptLine(models.Model):
    _name = 'hair.receipt.line'
    _description = 'Hair Stock Receipt Quantity'
    _check_company_auto = True

    receipt_id = fields.Many2one('hair.receipt', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='receipt_id.company_id', store=True)
    purchase_line_id = fields.Many2one('hair.purchase.line', required=True, check_company=True, ondelete='restrict', index=True)
    purchased_weight = fields.Float(related='purchase_line_id.payable_weight')
    cumulative_received_weight = fields.Float(related='purchase_line_id.received_weight', string='Cumulative Received kg')
    quantity = fields.Float(string='Received kg', required=True, digits=(16, 3))
    _source_unique = models.Constraint('UNIQUE(receipt_id, purchase_line_id)', 'Each purchase line can appear only once per receipt.')

    def _check_quantity_values(self, vals):
        if 'quantity' in vals:
            value = vals['quantity']
            if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                    or value <= 0 or round(value, 3) != value):
                raise ValidationError(self.env._('Receipt kg must be finite, positive and use 0.001 kg precision.'))
        if 'company_id' in vals:
            raise ValidationError(self.env._('Receipt company is derived from the purchase.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_quantity_values(vals)
            self.env['hair.receipt'].browse(vals.get('receipt_id', self.env.context.get('default_receipt_id')))._lock_draft()
        lines = super().create(vals_list)
        lines._check_source()
        return lines

    def write(self, vals):
        self.receipt_id._lock_draft()
        self._check_quantity_values(vals)
        if 'receipt_id' in vals:
            raise ValidationError(self.env._('A receipt line cannot be reassigned.'))
        result = super().write(vals)
        self._check_source()
        return result

    def unlink(self):
        self.receipt_id._lock_draft()
        return super().unlink()

    @api.constrains('purchase_line_id', 'receipt_id', 'quantity')
    def _check_source(self):
        for line in self:
            if line.purchase_line_id.purchase_id != line.receipt_id.purchase_id or line.quantity <= 0:
                raise ValidationError(self.env._('Receipt quantities must refer to a line of this purchase.'))
