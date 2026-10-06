from odoo import api, models
from odoo.exceptions import AccessError, ValidationError


class PurchaseReceipt(models.AbstractModel):
    _name = 'report.hair_purchase.purchase_receipt'
    _description = 'Hair Purchase Receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not self.env.su and not (self.env.user.has_group('hair_supplier.hair_supplier_group_buyer')
                                   or self.env.user.has_group('hair_purchase.hair_purchase_group_cashier')):
            raise AccessError(self.env._('Only hair buyers and cashiers may print purchase receipts.'))
        purchases = self.env['hair.purchase'].browse(docids).exists()
        purchases.check_access('read')
        if not purchases or len(purchases) != len(set(docids)) or any(not purchase.confirmed_date for purchase in purchases):
            raise ValidationError(self.env._('Purchase receipts require existing commercially confirmed purchases.'))
        return {'doc_ids': purchases.ids, 'doc_model': 'hair.purchase', 'docs': purchases}
