import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HairLength(models.Model):
    _name = 'hair.length'
    _inherit = 'hair.master'
    _description = 'Hair Length Definition'

    length_min = fields.Float(string='Minimum (inches)', required=True, default=0)
    length_max = fields.Float(string='Maximum (inches)', required=True, default=0)
    open_ended = fields.Boolean(string='No Upper Limit')

    @api.constrains('length_min', 'length_max', 'open_ended')
    def _check_bounds(self):
        for length in self:
            if (not math.isfinite(length.length_min)
                    or not math.isfinite(length.length_max)
                    or length.length_min < 0 or length.length_max < 0):
                raise ValidationError(self.env._('Lengths must be finite and nonnegative.'))
            if not length.open_ended and length.length_max < length.length_min:
                raise ValidationError(self.env._('Maximum length must be at least the minimum.'))
