from odoo import api, fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hair_intake_ids = fields.One2many('hair.purchase', 'seller_id', groups='hair_supplier.hair_supplier_group_buyer')
    hair_intake_count = fields.Integer('Intakes', compute='_compute_hair_intake_statistics', compute_sudo=False,
                                       groups='hair_supplier.hair_supplier_group_buyer')
    hair_intake_weight = fields.Float('Intake Payable Weight (kg)', compute='_compute_hair_intake_statistics',
                                     digits=(16, 3), compute_sudo=False, groups='hair_supplier.hair_supplier_group_buyer')
    hair_last_intake_date = fields.Datetime('Last Intake', compute='_compute_hair_intake_statistics', compute_sudo=False,
                                          groups='hair_supplier.hair_supplier_group_buyer')

    @api.depends('hair_intake_ids', 'hair_intake_ids.payable_weight', 'hair_intake_ids.date')
    @api.depends_context('uid', 'company')
    def _compute_hair_intake_statistics(self):
        # Aggregate with the caller's access rules; never expose hidden purchases.
        rows = self.env['hair.purchase']._read_group(
            [('seller_id', 'in', self.ids)], ['seller_id'], ['__count', 'payable_weight:sum', 'date:max'],
        )
        statistics = {seller.id: (count, weight, date) for seller, count, weight, date in rows}
        for seller in self:
            seller.hair_intake_count, seller.hair_intake_weight, seller.hair_last_intake_date = statistics.get(seller.id, (0, 0, False))

    def action_view_hair_intakes(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.su and not self.env.user.has_group('hair_supplier.hair_supplier_group_buyer'):
            raise AccessError(self.env._('Only hair buyers may view intake history.'))
        self.env['hair.purchase'].check_access('read')
        action = self.env['ir.actions.actions']._for_xml_id('hair_purchase.hair_purchase_action')
        action['domain'] = [('seller_id', '=', self.id)]
        action['context'] = {'default_seller_id': self.id, 'default_company_id': self.company_id.id}
        return action
