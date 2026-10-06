import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError

OVERRIDE_FIELDS = ('override_base_rate', 'override_by_id', 'override_date', 'override_reason')


class HairPurchase(models.Model):
    _inherit = 'hair.purchase'

    def _confirmation_quotes(self):
        quotes = super()._confirmation_quotes()
        for line, quote in quotes:
            if line.override_by_id:
                if line.override_base_rate != quote['price_per_kg']:
                    raise ValidationError(self.env._('The original pricing rate changed; compute and review pricing again.'))
                quote.update(price_per_kg=line.price_per_kg,
                             amount=self.currency_id.round(line.payable_weight * line.price_per_kg))
        return quotes


class HairPurchaseLine(models.Model):
    _inherit = 'hair.purchase.line'

    override_base_rate = fields.Float(readonly=True, copy=False, digits=0)
    override_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict')
    override_date = fields.Datetime(readonly=True, copy=False)
    override_reason = fields.Text(readonly=True, copy=False)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        values.update(dict.fromkeys(set(field_list) & set(OVERRIDE_FIELDS), False))
        return values

    def _check_weight_values(self, vals):
        super()._check_weight_values(vals)
        if set(OVERRIDE_FIELDS) & vals.keys():
            raise ValidationError(self.env._('Price override provenance can only be set by the authorized action.'))

    def _write_quality(self, vals):
        if 'price_per_kg' in vals or ('grade_id' in vals and not vals['grade_id']):
            vals = {**vals, **dict.fromkeys(OVERRIDE_FIELDS, False)}
        return super()._write_quality(vals)

    def action_override_price(self, rate, reason):
        self.ensure_one()
        purchase = self.purchase_id
        purchase._require_hair_role('hair_supplier.hair_supplier_group_manager')
        purchase._lock_quality_records()
        self.invalidate_recordset()
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
            raise ValidationError(self.env._('The override rate must be finite and positive.'))
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError(self.env._('A price override reason is required.'))
        # Confirmation performs the same freshness checks before any override is
        # applied. This helper validates without changing the workflow state.
        quotes = purchase._confirmation_quotes()
        if not purchase.quoted_date or purchase.quoted_currency_id != purchase.company_id.currency_id:
            raise ValidationError(self.env._('Compute and review pricing before overriding.'))
        for line, quote in quotes:
            if (line.pricing_rule_id.id != quote['rule_id'] or line.price_per_kg != quote['price_per_kg']
                    or line.amount != quote['amount'] or line.hair_type_snapshot != line.hair_type_id.display_name
                    or line.grade_snapshot != line.grade_id.display_name or line.length_snapshot != line.length_id.display_name
                    or line.length_min_snapshot != line.length_id.length_min or line.length_max_snapshot != line.length_id.length_max
                    or line.length_open_ended_snapshot != line.length_id.open_ended):
                raise ValidationError(self.env._('The quote changed; compute and review pricing again.'))
        amount = purchase.currency_id.round(self.payable_weight * rate)
        if not math.isfinite(amount):
            raise ValidationError(self.env._('The override amount must be finite.'))
        if self.price_per_kg == rate:
            return True
        previous = self.price_per_kg
        base_rate = self.override_base_rate if self.override_by_id else previous
        # Trusted private ORM helper preserves ACLs; no context bypass or sudo.
        super()._write_quality({'price_per_kg': rate, 'amount': amount, 'override_base_rate': base_rate,
                               'override_by_id': self.env.user.id, 'override_date': fields.Datetime.now(),
                               'override_reason': reason.strip()})
        purchase.message_post(body=self.env._(
            'Price override for line %(line)s: %(old)s → %(new)s %(currency)s/kg. Reason: %(reason)s',
            line=self.id, old=previous, new=rate, currency=purchase.currency_id.name, reason=reason.strip()))
        return True

    def action_open_price_override(self):
        self.ensure_one()
        self.purchase_id._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self.check_access('read')
        return {'type': 'ir.actions.act_window', 'name': self.env._('Override Price'),
                'res_model': 'hair.price.override.wizard', 'view_mode': 'form', 'target': 'new',
                'context': {'default_line_id': self.id, 'default_rate': self.price_per_kg}}


class HairPriceOverrideWizard(models.TransientModel):
    _name = 'hair.price.override.wizard'
    _description = 'Hair Price Override'

    line_id = fields.Many2one('hair.purchase.line', required=True, ondelete='cascade')
    rate = fields.Float(string='New Rate per kg', required=True, digits=0)
    reason = fields.Text(required=True)

    def action_apply(self):
        self.ensure_one()
        self.line_id.action_override_price(self.rate, self.reason)
        return {'type': 'ir.actions.act_window_close'}
