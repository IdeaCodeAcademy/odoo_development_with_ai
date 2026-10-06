from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hair_is_seller = fields.Boolean(string='Hair Seller', index=True)
    hair_seller_type_id = fields.Many2one(
        'hair.seller.type', string='Seller Type', ondelete='restrict',
        domain="[('company_id', '=', company_id)]",
    )
    hair_alternative_phone = fields.Char(string='Alternative Phone')
    hair_township = fields.Char(string='Township')
    hair_seller_notes = fields.Text(string='Seller Notes')
    hair_identification = fields.Char(
        string='Identification / NRC', copy=False,
        groups='hair_supplier.hair_supplier_group_manager',
    )

    @api.constrains('hair_is_seller', 'company_id', 'hair_seller_type_id', 'name')
    def _check_hair_seller(self):
        for seller in self.filtered('hair_is_seller'):
            if not seller.name or not seller.name.strip():
                raise ValidationError(self.env._('A seller name is required.'))
            if not seller.company_id:
                raise ValidationError(self.env._('Hair sellers must belong to a company.'))
            if seller.hair_seller_type_id and seller.hair_seller_type_id.company_id != seller.company_id:
                raise ValidationError(self.env._('Seller type and seller must belong to the same company.'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('hair_is_seller', self.env.context.get('default_hair_is_seller')) for vals in vals_list):
            self._check_hair_seller_permission()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('hair_is_seller') or self.filtered('hair_is_seller'):
            self._check_hair_seller_permission()
            if ('company_id' in vals and not self.env.su
                    and vals['company_id'] not in self.env.companies.ids):
                raise AccessError(self.env._('You cannot assign sellers to this company.'))
        return super().write(vals)

    def _check_hair_seller_permission(self):
        if not self.env.su and not self.env.user.has_group('hair_supplier.hair_supplier_group_buyer'):
            raise AccessError(self.env._('Only hair buyers and managers can create or edit sellers.'))
