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

    hair_purchase_count = fields.Integer('Confirmed Purchases', compute='_compute_hair_purchase_statistics',
                                         compute_sudo=False, groups='hair_supplier.hair_supplier_group_buyer')
    hair_purchase_weight = fields.Float('Purchased Weight (kg)', compute='_compute_hair_purchase_statistics',
                                       digits=(16, 3), compute_sudo=False, groups='hair_supplier.hair_supplier_group_buyer')
    hair_purchase_value_summary = fields.Char('Purchase Value by Currency', compute='_compute_hair_purchase_statistics',
                                             compute_sudo=False, groups='hair_supplier.hair_supplier_group_buyer')
    hair_last_purchase_date = fields.Datetime('Last Confirmed Purchase', compute='_compute_hair_purchase_statistics',
                                             compute_sudo=False, groups='hair_supplier.hair_supplier_group_buyer')

    @api.depends('hair_intake_ids', 'hair_intake_ids.state', 'hair_intake_ids.payable_weight',
                 'hair_intake_ids.amount_total', 'hair_intake_ids.confirmed_currency_id', 'hair_intake_ids.date')
    @api.depends_context('uid', 'company')
    def _compute_hair_purchase_statistics(self):
        rows = self.env['hair.purchase']._read_group(
            [('seller_id', 'in', self.ids), ('state', 'in', ['confirmed', 'paid', 'received'])],
            ['seller_id', 'confirmed_currency_id'], ['__count', 'payable_weight:sum', 'amount_total:sum', 'date:max'],
        )
        statistics = {}
        for seller, currency, count, weight, amount, date in rows:
            entry = statistics.setdefault(seller.id, {'count': 0, 'weight': 0, 'date': False, 'values': []})
            entry['count'] += count
            entry['weight'] += weight
            entry['date'] = max(entry['date'], date) if entry['date'] else date
            entry['values'].append((currency.name, f"{currency.round(amount):.{currency.decimal_places}f} {currency.name}"))
        for seller in self:
            entry = statistics.get(seller.id, {'count': 0, 'weight': 0, 'date': False, 'values': []})
            seller.hair_purchase_count = entry['count']
            seller.hair_purchase_weight = entry['weight']
            seller.hair_last_purchase_date = entry['date']
            # Keep historical currencies separate; no guessed conversion rates.
            seller.hair_purchase_value_summary = '; '.join(value for _currency, value in sorted(entry['values'])) or False

    def action_view_hair_purchases(self):
        action = self.action_view_hair_intakes()
        action['domain'].append(('state', 'in', ['confirmed', 'paid', 'received']))
        action['name'] = self.env._('Confirmed Hair Purchases')
        return action

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
