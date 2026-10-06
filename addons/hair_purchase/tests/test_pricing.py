from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairPricing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Foreign Pricing Company'})
        cls.admin = new_test_user(cls.env, login='price_admin', groups='hair_base.hair_base_group_manager',
                                 company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.buyer = new_test_user(cls.env, login='price_buyer', groups='hair_supplier.hair_supplier_group_buyer',
                                 company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.hair_type = cls.env['hair.type'].create({'name': 'Pricing Type'})
        cls.grade = cls.env['hair.grade'].create({'name': 'Pricing Grade'})
        cls.length = cls.env['hair.length'].create({'name': '10-14', 'length_min': 10, 'length_max': 14})
        cls.exact = cls.env['hair.length'].create({'name': '12', 'length_min': 12, 'length_max': 12})
        cls.Rule = cls.env['hair.pricing.rule'].with_user(cls.admin)

    def rule(self, **kwargs):
        return self.Rule.create({'name': 'Test kg rate', 'hair_type_id': self.hair_type.id,
                                 'grade_id': self.grade.id, 'length_id': self.length.id,
                                 'date_start': '2026-01-01', 'date_end': '2026-01-31',
                                 'price_per_kg': 123.456, **kwargs})

    def match(self, date='2026-01-15', length=None):
        return self.env['hair.pricing.rule'].with_user(self.buyer)._match_rule(
            self.company, self.hair_type, self.grade, length or self.exact, date)

    def test_effective_dates_and_range_matching(self):
        rule = self.rule()
        self.assertEqual(self.match('2026-01-01'), rule)
        self.assertEqual(self.match('2026-01-31'), rule)
        self.assertEqual(self.match().price_per_kg, 123.456)
        for date in ('2025-12-31', '2026-02-01'):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.match(date)
        next_rule = self.rule(date_start='2026-02-01', date_end=False)
        self.assertEqual(self.match('2027-01-01'), next_rule)

    def test_no_matching_grade_or_length_and_archived_rules(self):
        rule = self.rule()
        far = self.env['hair.length'].create({'name': '20', 'length_min': 20, 'length_max': 20})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.match(length=far)
        other_grade = self.env['hair.grade'].create({'name': 'Other Grade'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Rule._match_rule(self.company, self.hair_type, other_grade, self.exact, '2026-01-15')
        rule.write({'active': False})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Rule.with_context(active_test=False)._match_rule(self.company, self.hair_type, self.grade, self.exact, '2026-01-15')
        self.rule()

    def test_overlap_rejected_for_ranges_and_inclusive_dates(self):
        self.rule()
        for kwargs in ({}, {'length_id': self.exact.id}, {'date_start': '2026-01-31', 'date_end': False}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.rule(**kwargs)
        separate = self.env['hair.length'].create({'name': '15-18', 'length_min': 15, 'length_max': 18})
        rule = self.rule(length_id=separate.id)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            separate.write({'length_min': 14})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            rule.write({'length_id': self.length.id})

    def test_open_ended_length_overlap(self):
        long_length = self.env['hair.length'].create({'name': '27+', 'length_min': 27, 'open_ended': True})
        rule = self.rule(length_id=long_length.id)
        exact = self.env['hair.length'].create({'name': '30', 'length_min': 30, 'length_max': 30})
        self.assertEqual(self.match(length=exact), rule)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.rule(length_id=exact.id)

    def test_invalid_price_and_date_values(self):
        for value in (-1, 0, float('inf'), float('nan')):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    self.rule(price_per_kg=value)
        for kwargs in ({'date_end': '2025-01-01'}, {'name': '   '}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.rule(**kwargs)

    def test_permissions_and_company_isolation(self):
        rule = self.rule()
        with self.assertRaises(AccessError), self.cr.savepoint():
            rule.with_user(self.buyer).write({'price_per_kg': 999})
        with self.assertRaises(AccessError), self.cr.savepoint():
            rule.unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            rule.write({'company_id': self.other_company.id})
        values = {'name': 'Foreign Price', 'company_id': self.other_company.id, 'price_per_kg': 10, 'date_start': '2026-01-01'}
        for model, field in (('hair.type', 'hair_type_id'), ('hair.grade', 'grade_id'), ('hair.length', 'length_id')):
            values[field] = self.env[model].create({'name': 'Foreign Dimension', 'company_id': self.other_company.id}).id
        foreign = self.env['hair.pricing.rule'].create(values)
        self.assertFalse(self.Rule.search([('id', '=', foreign.id)]))
        with self.assertRaises(AccessError), self.cr.savepoint():
            foreign.with_user(self.admin).read(['price_per_kg'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.Rule.create(values)
        for user in (self.env.ref('base.public_user'), self.env.ref('base.template_portal_user_id')):
            with self.assertRaises(AccessError), self.cr.savepoint():
                rule.with_user(user).read(['price_per_kg'])

    def test_pricing_views_load(self):
        for view_type in ('list', 'form', 'search'):
            view = self.Rule.get_view(self.env.ref('hair_purchase.hair_pricing_rule_view_' + view_type).id, view_type)
            self.assertIn('hair_type_id', view['arch'])

    def test_quote_amount_uses_kg_and_currency_rounding(self):
        rule = self.rule()
        quote = self.Rule._quote(self.company, self.hair_type, self.grade, self.exact, '2026-01-15', .601)
        self.assertEqual(quote['rule_id'], rule.id)
        self.assertEqual(quote['price_per_kg'], 123.456)
        self.assertEqual(quote['amount'], self.company.currency_id.round(.601 * 123.456))
        for weight in (-1, 0, float('inf'), float('nan')):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.Rule._quote(self.company, self.hair_type, self.grade, self.exact, '2026-01-15', weight)
