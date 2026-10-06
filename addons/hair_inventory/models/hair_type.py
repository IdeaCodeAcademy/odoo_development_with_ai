from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HairType(models.Model):
    _inherit = 'hair.type'

    stock_product_id = fields.Many2one('product.product', string='Inventory Product',
                                      check_company=True, ondelete='restrict')

    @api.constrains('stock_product_id', 'company_id')
    def _check_stock_product(self):
        kg = self.env.ref('uom.product_uom_kgm')
        for hair_type in self:
            product = hair_type.stock_product_id
            if product and (not product.is_storable or product.tracking != 'lot' or product.uom_id != kg
                            or (product.company_id and product.company_id != hair_type.company_id)):
                raise ValidationError(self.env._('Hair inventory products must be stock-tracked goods with lot tracking, kg units and a compatible company.'))

    def _inventory_product(self):
        self.ensure_one()
        self.check_access('read')
        self._check_stock_product()
        product = self.stock_product_id
        if not product or not product.active:
            raise ValidationError(self.env._('Configure an active inventory product for this hair type before receiving stock.'))
        product.check_access('read')
        return product


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        result = super().write(vals)
        if {'is_storable', 'tracking', 'uom_id', 'company_id', 'type', 'store_by'} & vals.keys():
            # Narrow integrity validation across all mapped types, including other
            # companies using a shared product. No reads or mutations are exposed
            # to the caller; the original product write keeps standard ACLs.
            self.env['hair.type'].sudo().with_context(active_test=False).search([
                ('stock_product_id.product_tmpl_id', 'in', self.ids),
            ])._check_stock_product()
            sources = self.env['stock.move'].sudo().search([
                ('product_id.product_tmpl_id', 'in', self.ids), ('hair_receipt_line_id', '!=', False),
            ])
            for move in sources:
                product = move.product_id
                if (not product.is_storable or product.tracking != 'lot'
                        or product.uom_id != self.env.ref('uom.product_uom_kgm')
                        or (product.company_id and product.company_id != move.company_id)):
                    raise ValidationError(self.env._('A hair source receipt product must retain lot tracking, kg units and its compatible company.'))
        return result
