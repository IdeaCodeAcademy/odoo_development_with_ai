from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairIntake(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Foreign Intake Company'})
        cls.buyer = new_test_user(cls.env, login='intake_buyer', groups='hair_supplier.hair_supplier_group_buyer',
                                 company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.unrelated = new_test_user(cls.env, login='intake_unrelated', groups='base.group_user')
        cls.seller = cls.env['res.partner'].create({'name': 'Intake Seller', 'hair_is_seller': True, 'company_id': cls.company.id})
        cls.foreign_seller = cls.env['res.partner'].create({'name': 'Foreign Seller', 'hair_is_seller': True, 'company_id': cls.other_company.id})
        cls.Purchase = cls.env['hair.purchase'].with_user(cls.buyer)

    def intake(self):
        return self.Purchase.create({'seller_id': self.seller.id})

    def test_sequence_and_multiple_line_totals(self):
        purchase = self.intake()
        second = self.intake()
        self.assertTrue(purchase.name.startswith('HP/'))
        self.assertNotEqual(purchase.name, second.name)
        purchase.write({'line_ids': [
            Command.create({'gross_weight': 1.5, 'tare_weight': .1, 'waste_weight': .05, 'moisture_weight': .02, 'other_weight': .03}),
            Command.create({'gross_weight': .301, 'tare_weight': .1, 'waste_weight': .2}),
        ]})
        self.assertAlmostEqual(purchase.line_ids[0].payable_weight, 1.3)
        self.assertAlmostEqual(purchase.line_ids[1].payable_weight, .001)
        self.assertAlmostEqual(purchase.payable_weight, 1.301)
        purchase.line_ids[0].write({'gross_weight': 2})
        self.assertAlmostEqual(purchase.payable_weight, 1.801)
        purchase.line_ids[1].unlink()
        self.assertAlmostEqual(purchase.payable_weight, 1.8)

    def test_negative_nonfinite_and_excess_deductions(self):
        purchase = self.intake()
        Line = self.env['hair.purchase.line'].with_user(self.buyer)
        for field in ('gross_weight', 'tare_weight', 'waste_weight', 'moisture_weight', 'other_weight'):
            for value in (-1, float('inf'), float('nan')):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValidationError), self.cr.savepoint():
                        Line.create({'purchase_id': purchase.id, 'gross_weight': 1, field: value})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Line.create({'purchase_id': purchase.id, 'gross_weight': .3, 'tare_weight': .1, 'waste_weight': .201})
        line = Line.create({'purchase_id': purchase.id, 'gross_weight': .3, 'tare_weight': .1, 'waste_weight': .2})
        self.assertEqual(line.payable_weight, 0)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            line.write({'gross_weight': .299})

    def test_company_isolation_and_line_reassignment(self):
        local = self.intake()
        foreign = self.env['hair.purchase'].create({'company_id': self.other_company.id, 'seller_id': self.foreign_seller.id})
        line = self.env['hair.purchase.line'].with_user(self.buyer).create({'purchase_id': local.id, 'gross_weight': 1})
        self.assertFalse(self.Purchase.search([('id', '=', foreign.id)]))
        operations = (
            lambda: foreign.with_user(self.buyer).read(['name']),
            lambda: foreign.with_user(self.buyer).write({'notes': 'Forbidden'}),
            lambda: local.write({'company_id': self.other_company.id}),
            lambda: self.Purchase.create({'company_id': self.other_company.id, 'seller_id': self.foreign_seller.id}),
            lambda: line.write({'purchase_id': foreign.id}),
            lambda: line.create({'purchase_id': foreign.id}),
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                with self.assertRaises(AccessError), self.cr.savepoint():
                    operation()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            local.write({'seller_id': self.foreign_seller.id})
        foreign_type = self.env['hair.type'].create({'name': 'Foreign Type', 'company_id': self.other_company.id})
        with self.assertRaises(UserError), self.cr.savepoint():
            line.write({'hair_type_id': foreign_type.id})

    def test_unrelated_public_portal_denied_and_header_retained(self):
        purchase = self.intake()
        for user in (self.unrelated, self.env.ref('base.public_user'), self.env.ref('base.template_portal_user_id')):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError), self.cr.savepoint():
                    purchase.with_user(user).read(['name'])
                with self.assertRaises(AccessError), self.cr.savepoint():
                    self.env['hair.purchase'].with_user(user).create({'seller_id': self.seller.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            purchase.unlink()

    def test_seller_and_lifecycle_integrity(self):
        purchase = self.intake()
        contact = self.env['res.partner'].create({'name': 'Ordinary Contact', 'company_id': self.company.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.write({'seller_id': contact.id})
        for vals in ({'name': 'FORGED'}, {'state': 'confirmed'}, {'payable_weight': 999}, {'currency_id': self.company.currency_id.id}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                purchase.write(vals)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Purchase.create({'seller_id': self.seller.id, 'state': 'confirmed'})

    def test_views_load(self):
        for view_type in ('list', 'form', 'search'):
            view = self.Purchase.get_view(self.env.ref('hair_purchase.hair_purchase_view_' + view_type).id, view_type)
            self.assertIn('seller_id', view['arch'])

    def test_line_derived_fields_cannot_be_forged(self):
        purchase = self.intake()
        Line = self.env['hair.purchase.line'].with_user(self.buyer)
        line = Line.create({'purchase_id': purchase.id, 'gross_weight': 1})
        for vals in ({'payable_weight': 999}, {'company_id': self.other_company.id}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                line.write(vals)
            with self.assertRaises(ValidationError), self.cr.savepoint():
                Line.create({'purchase_id': purchase.id, **vals})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Purchase.create({'seller_id': self.seller.id, 'payable_weight': 999})
