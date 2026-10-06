import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class HairPricingRule(models.Model):
    _name = 'hair.pricing.rule'
    _description = 'Hair Price per Kilogram'
    _check_company_auto = True
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, ondelete='restrict', index=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    hair_type_id = fields.Many2one('hair.type', required=True, check_company=True, ondelete='restrict')
    grade_id = fields.Many2one('hair.grade', required=True, check_company=True, ondelete='restrict')
    length_id = fields.Many2one('hair.length', required=True, check_company=True, ondelete='restrict')
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date()
    price_per_kg = fields.Float('Price per kg', digits=0, required=True)

    @api.constrains('name', 'price_per_kg', 'date_start', 'date_end')
    def _check_values(self):
        for rule in self:
            if not rule.name.strip():
                raise ValidationError(self.env._('A pricing rule name is required.'))
            if not math.isfinite(rule.price_per_kg) or rule.price_per_kg <= 0:
                raise ValidationError(self.env._('Price per kg must be finite and positive.'))
            if rule.date_end and rule.date_end < rule.date_start:
                raise ValidationError(self.env._('The pricing end date cannot precede its start date.'))

    @api.constrains('active', 'company_id', 'hair_type_id', 'grade_id', 'length_id', 'date_start', 'date_end')
    def _check_overlap(self):
        for rule in self.filtered('active'):
            others = self.search([
                ('active', '=', True), ('id', '!=', rule.id), ('company_id', '=', rule.company_id.id),
                ('hair_type_id', '=', rule.hair_type_id.id), ('grade_id', '=', rule.grade_id.id),
            ])
            for other in others:
                dates_overlap = (not rule.date_end or other.date_start <= rule.date_end) and (not other.date_end or rule.date_start <= other.date_end)
                a, b = rule.length_id, other.length_id
                lengths_overlap = (b.length_min <= a.length_max or a.open_ended) and (a.length_min <= b.length_max or b.open_ended)
                if dates_overlap and lengths_overlap:
                    raise ValidationError(self.env._('Active pricing rules cannot overlap for the same company, type, grade, dates and lengths.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id', self.env.company.id)
            if not self.env.su and company_id not in self.env.companies.ids:
                raise AccessError(self.env._('You cannot configure prices for this company.'))
        return super().create(vals_list)

    def write(self, vals):
        if 'company_id' in vals and not self.env.su and vals['company_id'] not in self.env.companies.ids:
            raise AccessError(self.env._('You cannot configure prices for this company.'))
        return super().write(vals)

    @api.model
    def _match_rule(self, company, hair_type, grade, length, date):
        # Private selection API: caller must already be authorized for the intake.
        date = fields.Date.to_date(date)
        if not date or any(record.company_id != company for record in (hair_type, grade, length)):
            raise ValidationError(self.env._('Pricing dimensions must belong to the purchase company and include a date.'))
        rules = self.search([
            ('active', '=', True), ('company_id', '=', company.id), ('hair_type_id', '=', hair_type.id),
            ('grade_id', '=', grade.id), ('date_start', '<=', date),
            '|', ('date_end', '=', False), ('date_end', '>=', date),
        ]).filtered(lambda rule: rule.length_id.length_min <= length.length_min and (
            rule.length_id.open_ended or (not length.open_ended and rule.length_id.length_max >= length.length_max)
        ))
        if len(rules) != 1:
            raise ValidationError(self.env._('Exactly one active pricing rule must cover the hair length and purchase date.'))
        return rules

    @api.model
    def _quote(self, company, hair_type, grade, length, date, payable_weight):
        if not math.isfinite(payable_weight) or payable_weight <= 0:
            raise ValidationError(self.env._('Pricing requires a finite, positive payable weight in kg.'))
        rule = self._match_rule(company, hair_type, grade, length, date)
        return {
            'rule_id': rule.id,
            'price_per_kg': rule.price_per_kg,
            'currency_id': company.currency_id.id,
            'amount': company.currency_id.round(payable_weight * rule.price_per_kg),
        }


class HairLength(models.Model):
    _inherit = 'hair.length'

    def write(self, vals):
        result = super().write(vals)
        if {'length_min', 'length_max', 'open_ended'} & vals.keys():
            # Changes to shared bounds must also preserve pricing consistency.
            # Narrow sudo validates all affected rules, including hidden companies;
            # it does not grant the caller mutation/read access to those rules.
            self.env['hair.pricing.rule'].sudo().search([('length_id', 'in', self.ids)])._check_overlap()
        return result
