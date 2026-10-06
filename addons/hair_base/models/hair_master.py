from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class HairMaster(models.AbstractModel):
    _name = 'hair.master'
    _description = 'Hair Master Data'
    _order = 'sequence, name, id'
    _check_company_auto = True

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company,
        index=True, ondelete='restrict',
    )

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(self.env._('A name is required.'))

    def write(self, vals):
        # Odoo 20 constraints run in sudo; authorize company changes before write.
        if ('company_id' in vals and not self.env.su
                and vals['company_id'] not in self.env.companies.ids):
            raise AccessError(self.env._('You cannot configure hair data for this company.'))
        return super().write(vals)


class HairType(models.Model):
    _name = 'hair.type'
    _inherit = 'hair.master'
    _description = 'Hair Type'


class HairTexture(models.Model):
    _name = 'hair.texture'
    _inherit = 'hair.master'
    _description = 'Hair Texture'


class HairColor(models.Model):
    _name = 'hair.color'
    _inherit = 'hair.master'
    _description = 'Hair Color'


class HairGrade(models.Model):
    _name = 'hair.grade'
    _inherit = 'hair.master'
    _description = 'Hair Grade'
