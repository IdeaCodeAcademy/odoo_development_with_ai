from odoo import models


class HairSellerType(models.Model):
    _name = 'hair.seller.type'
    _inherit = 'hair.master'
    _description = 'Hair Seller Type'
