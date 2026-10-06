import math
import uuid

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class HairPaymentMethod(models.Model):
    _name = 'hair.payment.method'
    _inherit = 'hair.master'
    _description = 'Hair Payment Method'


class HairPurchase(models.Model):
    _inherit = 'hair.purchase'

    state = fields.Selection(selection_add=[('paid', 'Paid')], ondelete={'paid': 'set default'})
    payment_ids = fields.One2many('hair.purchase.payment', 'purchase_id', readonly=True, copy=False,
                                 groups='hair_supplier.hair_supplier_group_buyer,hair_purchase.hair_purchase_group_cashier')
    # Stored aggregates intentionally use standard compute_sudo: read-only totals
    # remain available to purchase readers without exposing payment details.
    paid_amount = fields.Monetary(compute='_compute_payments', store=True, currency_field='currency_id')
    balance_amount = fields.Monetary(compute='_compute_payments', store=True, currency_field='currency_id')
    payment_status = fields.Selection([('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid')],
                                      compute='_compute_payments', store=True)

    @api.depends('payment_ids.state', 'payment_ids.amount', 'amount_total')
    def _compute_payments(self):
        for purchase in self:
            purchase.paid_amount = math.fsum(purchase.payment_ids.filtered(lambda payment: payment.state == 'posted').mapped('amount'))
            purchase.balance_amount = purchase.amount_total - purchase.paid_amount
            purchase.payment_status = ('unpaid' if not purchase.paid_amount else
                                       'paid' if purchase.balance_amount <= 0 else 'partial')

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in ('payment_ids', 'paid_amount', 'balance_amount', 'payment_status'):
            if name in field_list:
                values[name] = [] if name == 'payment_ids' else 'unpaid' if name == 'payment_status' else 0
        return values

    def _check_derived_values(self, vals):
        super()._check_derived_values(vals)
        if {'payment_ids', 'paid_amount', 'balance_amount', 'payment_status'} & vals.keys():
            raise ValidationError(self.env._('Payments and payment totals can only change through payment records.'))

    def action_confirm_purchase(self):
        self.ensure_one()
        self._require_hair_role('hair_supplier.hair_supplier_group_manager')
        self._lock_quality_records()
        if self.state == 'paid':
            return True
        return super().action_confirm_purchase()

    def action_cancel_purchase(self):
        self._lock_quality_records()
        if any(purchase.paid_amount for purchase in self):
            raise ValidationError(self.env._('A purchase with posted payments requires a reversal workflow before cancellation.'))
        return super().action_cancel_purchase()


class HairPurchasePayment(models.Model):
    _name = 'hair.purchase.payment'
    _description = 'Hair Purchase Payment Record'
    _order = 'date desc, id desc'
    _check_company_auto = True

    request_key = fields.Char(required=True, default=lambda self: str(uuid.uuid4()), readonly=True, copy=False)
    _request_key_unique = models.Constraint('UNIQUE(request_key)', 'The payment request has already been recorded.')

    purchase_id = fields.Many2one('hair.purchase', required=True, index=True, ondelete='restrict')
    company_id = fields.Many2one(related='purchase_id.company_id', store=True, index=True)
    seller_id = fields.Many2one(related='purchase_id.seller_id', store=True)
    currency_id = fields.Many2one(related='purchase_id.confirmed_currency_id', store=True)
    amount = fields.Monetary(required=True, currency_field='currency_id')
    date = fields.Date(required=True, default=fields.Date.context_today)
    method_id = fields.Many2one('hair.payment.method', required=True, check_company=True, ondelete='restrict')
    reference = fields.Char()
    notes = fields.Text()
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default='draft', required=True, readonly=True, copy=False)
    posted_by_id = fields.Many2one('res.users', readonly=True, copy=False, ondelete='restrict')
    posted_date = fields.Datetime(readonly=True, copy=False)

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        for name in ('state', 'posted_by_id', 'posted_date', 'company_id', 'seller_id', 'currency_id'):
            if name in field_list:
                values[name] = 'draft' if name == 'state' else False
        return values

    def _require_cashier(self):
        if not self.env.su and not self.env.user.has_group('hair_purchase.hair_purchase_group_cashier'):
            raise AccessError(self.env._('Only cashiers may record purchase payments.'))

    def _validate_values(self, vals):
        if {'posted_by_id', 'posted_date', 'company_id', 'seller_id', 'currency_id'} & vals.keys() or vals.get('state', 'draft') != 'draft':
            raise ValidationError(self.env._('Payment provenance can only be set by posting.'))
        if 'amount' in vals:
            amount = vals['amount']
            if isinstance(amount, bool) or not isinstance(amount, (float, int)) or not math.isfinite(amount) or amount <= 0:
                raise ValidationError(self.env._('Payment amount must be finite and positive.'))

    def _validate_draft(self):
        for payment in self:
            if payment.purchase_id.state != 'confirmed':
                raise ValidationError(self.env._('Payments require a confirmed purchase with an outstanding balance.'))
            if not payment.method_id.active or payment.method_id.company_id != payment.company_id:
                raise ValidationError(self.env._('Select an active payment method for the purchase company.'))
            if payment.currency_id.round(payment.amount) <= 0 or payment.currency_id.round(payment.amount) != payment.amount:
                raise ValidationError(self.env._('Use a positive payment amount at the purchase currency precision.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._require_cashier()
        for vals in vals_list:
            self._validate_values(vals)
            purchase = self.env['hair.purchase'].browse(vals.get('purchase_id', self.env.context.get('default_purchase_id')))
            purchase._lock_quality_records()
            method = self.env['hair.payment.method'].browse(vals.get('method_id', self.env.context.get('default_method_id')))
            method.check_access('read')
            if 'amount' in vals and purchase.currency_id.round(vals['amount']) != vals['amount']:
                raise ValidationError(self.env._('Payment amount must use the purchase currency precision.'))
        payments = super().create(vals_list)
        payments._validate_draft()
        return payments

    def write(self, vals):
        self._require_cashier()
        self.check_access('write')
        self.purchase_id._lock_quality_records()
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()
        if any(payment.state != 'draft' for payment in self):
            raise ValidationError(self.env._('Posted payment records cannot be modified.'))
        self._validate_values(vals)
        if {'purchase_id', 'request_key'} & vals.keys():
            raise ValidationError(self.env._('A payment cannot be moved to another purchase.'))
        if vals.get('method_id'):
            self.env['hair.payment.method'].browse(vals['method_id']).check_access('read')
        if 'amount' in vals and any(payment.currency_id.round(vals['amount']) != vals['amount'] for payment in self):
            raise ValidationError(self.env._('Payment amount must use the purchase currency precision.'))
        result = super().write(vals)
        self._validate_draft()
        return result

    def unlink(self):
        self._require_cashier()
        self.check_access('unlink')
        self.purchase_id._lock_quality_records()
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()
        if any(payment.state != 'draft' for payment in self):
            raise ValidationError(self.env._('Posted payment records cannot be deleted.'))
        return super().unlink()

    def action_post(self):
        self.ensure_one()
        self._require_cashier()
        self.check_access('write')
        purchase = self.purchase_id
        purchase._lock_quality_records()
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset()
        if self.state == 'posted':
            return True
        self._validate_draft()
        if self.currency_id.compare_amounts(self.amount, purchase.balance_amount) > 0:
            raise ValidationError(self.env._('Payment exceeds the remaining purchase balance.'))
        # Private action's super write retains ORM ACLs without context or sudo.
        super().write({'state': 'posted', 'posted_by_id': self.env.user.id, 'posted_date': fields.Datetime.now()})
        if self.currency_id.is_zero(purchase.balance_amount):
            purchase._write_workflow({'state': 'paid'})
        purchase.message_post(body=self.env._('Payment recorded: %(amount)s %(currency)s via %(method)s. Reference: %(reference)s',
                                             amount=self.amount, currency=self.currency_id.name,
                                             method=self.method_id.display_name, reference=self.reference or ''))
        return True
