from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairConfirmation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.buyer = new_test_user(cls.env, login='confirm_buyer', groups='hair_supplier.hair_supplier_group_buyer')
        cls.officer = new_test_user(cls.env, login='confirm_officer', groups='hair_purchase.hair_purchase_group_quality')
        cls.manager = new_test_user(cls.env, login='confirm_manager', groups='hair_supplier.hair_supplier_group_manager')
        cls.seller = cls.env['res.partner'].create({'name': 'Original Seller', 'hair_is_seller': True, 'company_id': cls.company.id})
        cls.hair_type = cls.env['hair.type'].create({'name': 'Original Type'})
        cls.length = cls.env['hair.length'].create({'name': 'Original Length', 'length_min': 12, 'length_max': 14})
        cls.grade = cls.env['hair.grade'].create({'name': 'Original Grade'})
        cls.rule = cls.env['hair.pricing.rule'].create({'name': 'Synthetic Test Rate', 'hair_type_id': cls.hair_type.id,
                                                      'grade_id': cls.grade.id, 'length_id': cls.length.id,
                                                      'date_start': '2026-01-01', 'price_per_kg': 123.456})

    def intake(self, approve=True, quote=True):
        purchase = self.env['hair.purchase'].with_user(self.buyer).create({
            'seller_id': self.seller.id, 'date': '2026-01-02 10:00:00', 'line_ids': [Command.create({
                'hair_type_id': self.hair_type.id, 'length_id': self.length.id, 'gross_weight': .601,
            })],
        })
        if approve:
            purchase.action_submit_inspection()
            purchase.with_user(self.officer).line_ids.write({'proposed_grade_id': self.grade.id})
            purchase.with_user(self.officer).action_approve_quality()
        purchase = purchase.with_user(self.manager)
        if approve and quote:
            purchase.action_quote_purchase()
        return purchase

    def test_confirmation_snapshots_and_retry_safety(self):
        purchase = self.intake()
        purchase.action_confirm_purchase()
        date = purchase.confirmed_date
        self.assertEqual(purchase.state, 'confirmed')
        self.assertEqual(purchase.confirmed_by_id, self.manager)
        self.assertEqual(purchase.seller_name_snapshot, 'Original Seller')
        self.assertEqual(purchase.line_ids.pricing_rule_id, self.rule)
        self.assertEqual(purchase.line_ids.price_per_kg, 123.456)
        self.assertEqual(purchase.amount_total, self.company.currency_id.round(.601 * 123.456))
        self.rule.write({'price_per_kg': 999})
        purchase.action_confirm_purchase()
        self.assertEqual(purchase.confirmed_date, date)
        self.assertEqual(purchase.line_ids.price_per_kg, 123.456)

    def test_configuration_changes_preserve_historical_values(self):
        purchase = self.intake()
        purchase.action_confirm_purchase()
        amount, currency = purchase.amount_total, purchase.currency_id
        self.rule.write({'price_per_kg': 999, 'active': False})
        self.seller.write({'name': 'Changed Seller'})
        self.grade.write({'name': 'Changed Grade'})
        self.hair_type.write({'name': 'Changed Type'})
        self.length.write({'name': 'Changed Length', 'length_min': 15, 'length_max': 18})
        other_currency = self.env['res.currency'].with_context(active_test=False).search([('id', '!=', currency.id)], limit=1)
        other_currency.write({'active': True})
        self.company.write({'currency_id': other_currency.id})
        self.assertEqual(purchase.currency_id, currency)
        self.assertEqual(purchase.amount_total, amount)
        self.assertEqual(purchase.line_ids.grade_snapshot, 'Original Grade')
        self.assertEqual(purchase.line_ids.hair_type_snapshot, 'Original Type')
        self.assertEqual(purchase.line_ids.length_snapshot, 'Original Length')
        self.assertEqual(purchase.line_ids.length_min_snapshot, 12)
        self.assertEqual(purchase.line_ids.length_max_snapshot, 14)
        self.assertEqual(purchase.seller_name_snapshot, 'Original Seller')

    def test_confirmation_requires_quality_and_applicable_prices(self):
        draft = self.intake(approve=False)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            draft.action_confirm_purchase()
        draft.with_user(self.buyer).action_submit_inspection()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            draft.action_confirm_purchase()
        approved = self.intake(quote=False)
        self.rule.write({'active': False})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            approved.action_confirm_purchase()
        self.assertEqual(approved.state, 'inspection')
        self.assertFalse(approved.confirmed_by_id)
        self.assertFalse(approved.line_ids.pricing_rule_id)
        self.assertEqual(approved.amount_total, 0)

    def test_confirmed_values_and_snapshot_forgery_are_blocked(self):
        purchase = self.intake()
        for vals in ({'amount_total': 999}, {'confirmed_currency_id': self.company.currency_id.id}, {'confirmed_by_id': self.manager.id}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                purchase.write(vals)
        for vals in ({'price_per_kg': 999}, {'amount': 999}, {'grade_snapshot': 'Forged'}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                purchase.line_ids.write(vals)
        purchase.action_confirm_purchase()
        for operation in (
            lambda: purchase.line_ids.write({'gross_weight': 2}),
            lambda: purchase.write({'seller_id': self.seller.id}),
            lambda: purchase.write({'date': '2026-01-03 10:00:00'}),
            purchase.action_return_to_draft,
        ):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                operation()
        duplicate = purchase.with_user(self.buyer).copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.confirmed_by_id)
        self.assertFalse(duplicate.line_ids.pricing_rule_id)
        self.assertEqual(duplicate.amount_total, 0)

    def test_buyer_and_quality_officer_cannot_confirm_or_cancel(self):
        purchase = self.intake()
        for user in (self.buyer, self.officer, self.env.ref('base.public_user')):
            for action in ('action_quote_purchase', 'action_confirm_purchase', 'action_cancel_purchase'):
                with self.assertRaises(AccessError), self.cr.savepoint():
                    getattr(purchase.with_user(user), action)()
        with self.assertRaises(AccessError), self.cr.savepoint():
            purchase.with_user(self.buyer).write({'cancellation_reason': 'Not authorized'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['hair.purchase'].with_user(self.buyer).create({'seller_id': self.seller.id, 'cancellation_reason': 'Forged reason'})

    def test_cancellation_requires_reason_and_preserves_snapshot(self):
        purchase = self.intake()
        purchase.action_confirm_purchase()
        amount = purchase.amount_total
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_cancel_purchase()
        purchase.write({'cancellation_reason': 'Seller declined commercial purchase'})
        purchase.action_cancel_purchase()
        date = purchase.cancelled_date
        purchase.action_cancel_purchase()
        self.assertEqual(purchase.state, 'cancelled')
        self.assertEqual(purchase.amount_total, amount)
        self.assertEqual(purchase.cancelled_by_id, self.manager)
        self.assertEqual(purchase.cancelled_date, date)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_confirm_purchase()

    def test_foreign_company_actions_denied(self):
        company = self.env['res.company'].create({'name': 'Foreign Confirm Company'})
        seller = self.env['res.partner'].create({'name': 'Foreign Seller', 'hair_is_seller': True, 'company_id': company.id})
        foreign = self.env['hair.purchase'].create({'seller_id': seller.id, 'company_id': company.id})
        for action in ('action_quote_purchase', 'action_confirm_purchase', 'action_cancel_purchase'):
            with self.assertRaises(AccessError), self.cr.savepoint():
                getattr(foreign.with_user(self.manager), action)()

    def test_quote_review_and_stale_rate_require_repricing(self):
        purchase = self.intake(quote=False)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_confirm_purchase()
        purchase.action_quote_purchase()
        self.assertEqual(purchase.state, 'inspection')
        self.assertEqual(purchase.quoted_by_id, self.manager)
        self.assertEqual(purchase.amount_total, self.company.currency_id.round(.601 * 123.456))
        self.rule.write({'price_per_kg': 200})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_confirm_purchase()
        self.assertEqual(purchase.line_ids.price_per_kg, 123.456)
        purchase.action_quote_purchase()
        self.assertEqual(purchase.line_ids.price_per_kg, 200)
        purchase.action_confirm_purchase()
        self.assertEqual(purchase.state, 'confirmed')

    def test_quote_clears_when_quality_returns_to_draft(self):
        purchase = self.intake()
        purchase.write({'revision_reason': 'Correct intake before commercial approval'})
        purchase.action_return_to_draft()
        self.assertEqual(purchase.state, 'draft')
        self.assertFalse(purchase.quoted_currency_id)
        self.assertFalse(purchase.quoted_date)
        self.assertFalse(purchase.line_ids.pricing_rule_id)
        self.assertEqual(purchase.line_ids.amount, 0)
        self.assertEqual(purchase.amount_total, 0)
