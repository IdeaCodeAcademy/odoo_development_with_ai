from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hair_receipt_id = fields.Many2one('hair.receipt', readonly=True, copy=False, ondelete='restrict')
    _hair_receipt_unique = models.Constraint('UNIQUE(hair_receipt_id)', 'A hair receipt can create only one stock transfer.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('hair_receipt_id') or self.env.context.get('default_hair_receipt_id'):
                raise ValidationError(self.env._('Hair receipt links can only be set by receipt posting.'))
            return_id = vals.get('return_id', self.env.context.get('default_return_id'))
            if return_id and self.browse(return_id).hair_receipt_id:
                raise ValidationError(self.env._('Hair receipt returns require an approved reversal workflow.'))
        return super().create(vals_list)

    @api.model
    def _create_hair_receipt(self, vals):
        return super().create(vals)

    def write(self, vals):
        if 'hair_receipt_id' in vals:
            raise ValidationError(self.env._('Hair receipt links cannot be changed.'))
        if self.filtered('hair_receipt_id') and {'company_id', 'location_id', 'location_dest_id', 'picking_type_id', 'return_id', 'move_ids', 'move_line_ids', 'state'} & vals.keys():
            if any(picking.state == 'done' for picking in self.filtered('hair_receipt_id')):
                raise ValidationError(self.env._('Completed hair receipt transfers cannot be rewritten.'))
        return super().write(vals)

    def _create_return(self):
        if self.filtered('hair_receipt_id'):
            raise ValidationError(self.env._('Hair receipt returns require an approved reversal workflow.'))
        return super()._create_return()


class StockLot(models.Model):
    _inherit = 'stock.lot'

    hair_receipt_line_id = fields.Many2one('hair.receipt.line', readonly=True, copy=False, ondelete='restrict')
    hair_purchase_line_id = fields.Many2one(related='hair_receipt_line_id.purchase_line_id')
    hair_purchase_id = fields.Many2one(related='hair_purchase_line_id.purchase_id')
    hair_seller_snapshot = fields.Char(related='hair_purchase_id.seller_name_snapshot')
    hair_type_snapshot = fields.Char(related='hair_purchase_line_id.hair_type_snapshot')
    hair_purchase_date = fields.Datetime(related='hair_purchase_id.date')
    hair_grade_snapshot = fields.Char(related='hair_purchase_line_id.grade_snapshot')
    hair_length_snapshot = fields.Char(related='hair_purchase_line_id.length_snapshot')
    hair_original_weight = fields.Float(related='hair_receipt_line_id.quantity')
    _hair_receipt_line_unique = models.Constraint('UNIQUE(hair_receipt_line_id)', 'A receipt line has only one source lot.')

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('hair_receipt_line_id') for vals in vals_list) or self.env.context.get('default_hair_receipt_line_id'):
            raise ValidationError(self.env._('Hair source lots can only be created by receipt posting.'))
        return super().create(vals_list)

    @api.model
    def _create_hair_receipt(self, vals):
        return super().create(vals)

    def unlink(self):
        if self.filtered('hair_receipt_line_id'):
            raise ValidationError(self.env._('Hair source lots must be retained for traceability.'))
        return super().unlink()

    def write(self, vals):
        if 'hair_receipt_line_id' in vals or (self.filtered('hair_receipt_line_id') and {'product_id', 'company_id'} & vals.keys()):
            raise ValidationError(self.env._('Hair lot source, product and company cannot change.'))
        return super().write(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    hair_receipt_line_id = fields.Many2one('hair.receipt.line', readonly=True, copy=False, ondelete='restrict')
    _hair_receipt_line_unique = models.Constraint('UNIQUE(hair_receipt_line_id)', 'A receipt line has only one source stock move.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('hair_receipt_line_id') or self.env.context.get('default_hair_receipt_line_id'):
                raise ValidationError(self.env._('Hair source moves can only be created by receipt posting.'))
            picking = self.env['stock.picking'].browse(vals.get('picking_id', self.env.context.get('default_picking_id')))
            if picking.hair_receipt_id:
                raise ValidationError(self.env._('Hair receipt transfers cannot gain additional stock moves.'))
            returned_move = vals.get('origin_returned_move_id', self.env.context.get('default_origin_returned_move_id'))
            if returned_move and self.browse(returned_move).hair_receipt_line_id:
                raise ValidationError(self.env._('Hair source returns require an approved reversal workflow.'))
        return super().create(vals_list)

    @api.model
    def _create_hair_receipt(self, vals):
        return super().create(vals)

    def write(self, vals):
        if 'hair_receipt_line_id' in vals:
            raise ValidationError(self.env._('Hair stock source links cannot change.'))
        if self.filtered('hair_receipt_line_id') and {'product_id', 'company_id', 'picking_id', 'location_id', 'location_dest_id', 'uom_id', 'product_uom_qty', 'quantity', 'move_line_ids', 'state'} & vals.keys():
            if any(move.state == 'done' for move in self.filtered('hair_receipt_line_id')):
                raise ValidationError(self.env._('Completed hair source moves cannot be changed.'))
        return super().write(vals)

    def _action_done(self, cancel_backorder=False):
        for move in self:
            source = move.hair_receipt_line_id
            if source:
                source.receipt_id._check_paid()
                if (move.picking_id.hair_receipt_id != source.receipt_id or move.company_id != source.company_id
                        or move.location_id.usage != 'supplier' or move.location_dest_id.usage != 'internal'
                        or move.uom_id != self.env.ref('uom.product_uom_kgm')
                        or float_compare(move.quantity, source.quantity, precision_digits=3) != 0):
                    raise ValidationError(self.env._('Hair stock movement must match the paid receipt quantity and company.'))
                if source.receipt_id.state != 'draft' and move.state != 'done':
                    raise ValidationError(self.env._('This hair receipt is already complete.'))
            for detail in move.move_line_ids:
                lot_source = detail.lot_id.hair_receipt_line_id
                if detail.location_id.usage == 'supplier' and lot_source and lot_source != source:
                    raise ValidationError(self.env._('A hair source lot cannot be received outside its original receipt.'))
        return super()._action_done(cancel_backorder=cancel_backorder)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            move = self.env['stock.move'].browse(vals.get('move_id', self.env.context.get('default_move_id')))
            picking = self.env['stock.picking'].browse(vals.get('picking_id', self.env.context.get('default_picking_id')))
            if picking.hair_receipt_id and not move.hair_receipt_line_id:
                raise ValidationError(self.env._('Hair receipt details require their original source move.'))
            if move.hair_receipt_line_id and move.state == 'done':
                raise ValidationError(self.env._('Completed hair receipts cannot gain additional stock details.'))
        return super().create(vals_list)

    @api.constrains('lot_id', 'move_id', 'location_id')
    def _check_hair_source_lot(self):
        for detail in self:
            source = detail.lot_id.hair_receipt_line_id
            if detail.location_id.usage == 'supplier' and source and detail.move_id.hair_receipt_line_id != source:
                raise ValidationError(self.env._('A hair source lot cannot be received outside its original receipt.'))

    def write(self, vals):
        if self.filtered(lambda line: line.move_id.hair_receipt_line_id and line.move_id.state == 'done'):
            if {'quantity', 'product_id', 'lot_id', 'lot_name', 'move_id', 'location_id', 'location_dest_id', 'uom_id', 'company_id'} & vals.keys():
                raise ValidationError(self.env._('Completed hair receipt quantities and lots cannot be changed.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda line: line.move_id.hair_receipt_line_id and line.move_id.state == 'done'):
            raise ValidationError(self.env._('Completed hair receipt details cannot be deleted.'))
        return super().unlink()
