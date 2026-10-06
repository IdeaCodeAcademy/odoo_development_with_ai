from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestSellerIntakeHistory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.buyer = new_test_user(cls.env, login='history_buyer', groups='hair_supplier.hair_supplier_group_buyer',
                                 company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.unrelated = new_test_user(cls.env, login='history_contact', groups='base.group_partner_manager')
        cls.seller = cls.env['res.partner'].create({'name': 'History Seller', 'hair_is_seller': True, 'company_id': cls.company.id})
        cls.Purchase = cls.env['hair.purchase'].with_user(cls.buyer)

    def test_aggregate_recomputes_with_intake_changes(self):
        seller = self.seller.with_user(self.buyer)
        self.assertEqual(seller.hair_intake_count, 0)
        self.assertFalse(seller.hair_last_intake_date)
        first = self.Purchase.create({'seller_id': seller.id, 'date': '2026-01-01 10:00:00',
                                      'line_ids': [Command.create({'gross_weight': 1, 'tare_weight': .1})]})
        second = self.Purchase.create({'seller_id': seller.id, 'date': '2026-01-02 10:00:00',
                                       'line_ids': [Command.create({'gross_weight': .601})]})
        self.assertEqual(seller.hair_intake_count, 2)
        self.assertAlmostEqual(seller.hair_intake_weight, 1.501)
        self.assertEqual(seller.hair_last_intake_date, second.date)
        first.line_ids.write({'gross_weight': 2})
        self.assertAlmostEqual(seller.hair_intake_weight, 2.501)
        other = self.env['res.partner'].create({'name': 'Another Seller', 'hair_is_seller': True, 'company_id': self.company.id})
        second.write({'seller_id': other.id})
        self.assertEqual(seller.hair_intake_count, 1)
        self.assertEqual(seller.hair_last_intake_date, first.date)
        self.assertAlmostEqual(other.with_user(self.buyer).hair_intake_weight, .601)

    def test_action_filters_seller_and_defaults_company(self):
        action = self.seller.with_user(self.buyer).action_view_hair_intakes()
        self.assertEqual(action['res_model'], 'hair.purchase')
        self.assertEqual(action['domain'], [('seller_id', '=', self.seller.id)])
        self.assertEqual(action['context']['default_company_id'], self.company.id)
        self.assertEqual(action['context']['default_seller_id'], self.seller.id)

    def test_unauthorized_statistics_and_action_denied(self):
        for user in (self.unrelated, self.env.ref('base.public_user'), self.env.ref('base.template_portal_user_id')):
            with self.subTest(user=user.login):
                seller = self.seller.with_user(user)
                with self.assertRaises(AccessError), self.cr.savepoint():
                    seller.read(['hair_intake_count', 'hair_intake_weight', 'hair_last_intake_date'])
                with self.assertRaises(AccessError), self.cr.savepoint():
                    seller.action_view_hair_intakes()

    def test_foreign_seller_history_is_not_exposed(self):
        company = self.env['res.company'].create({'name': 'Foreign History Company'})
        seller = self.env['res.partner'].create({'name': 'Foreign Seller', 'hair_is_seller': True, 'company_id': company.id})
        self.env['hair.purchase'].create({'seller_id': seller.id, 'company_id': company.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            seller.with_user(self.buyer).read(['hair_intake_count'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            seller.with_user(self.buyer).action_view_hair_intakes()
        self.assertEqual(self.seller.with_user(self.buyer).hair_intake_count, 0)
