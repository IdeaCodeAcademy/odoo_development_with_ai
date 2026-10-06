from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairSellers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Other Seller Company'})
        cls.buyer = new_test_user(
            cls.env, login='seller_buyer', groups='hair_supplier.hair_supplier_group_buyer',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.manager = new_test_user(
            cls.env, login='seller_manager', groups='hair_supplier.hair_supplier_group_manager',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.contact_manager = new_test_user(
            cls.env, login='unrelated_contacts', groups='base.group_partner_manager',
        )
        cls.seller_type = cls.env['hair.seller.type'].create({'name': 'Collector'})
        cls.seller = cls.env['res.partner'].create({
            'name': 'Test Seller', 'hair_is_seller': True, 'company_id': cls.company.id,
            'hair_seller_type_id': cls.seller_type.id, 'hair_identification': 'TEST-NRC',
        })

    def test_buyer_create_edit_archive_seller(self):
        Partner = self.env['res.partner'].with_user(self.buyer)
        seller = Partner.create({
            'name': 'Buyer Seller', 'hair_is_seller': True, 'company_id': self.company.id,
            'hair_seller_type_id': self.seller_type.id, 'phone': 'TEST-PHONE',
        })
        seller.write({'hair_township': 'Test Township', 'hair_alternative_phone': 'TEST-ALT'})
        self.assertEqual(seller.hair_township, 'Test Township')
        seller.write({'active': False})
        self.assertFalse(Partner.search([('id', '=', seller.id)]))
        with self.assertRaises(AccessError), self.cr.savepoint():
            seller.unlink()

    def test_manager_nrc_access_and_buyer_protection(self):
        self.seller.with_user(self.manager).write({'hair_identification': 'TEST-UPDATED'})
        self.assertEqual(self.seller.with_user(self.manager).read(['hair_identification'])[0]['hair_identification'], 'TEST-UPDATED')
        buyer_seller = self.seller.with_user(self.buyer)
        self.assertNotIn('hair_identification', buyer_seller.fields_get())
        operations = (
            lambda: buyer_seller.read(['hair_identification']),
            lambda: buyer_seller.write({'hair_identification': 'FORBIDDEN'}),
            lambda: buyer_seller.search([('hair_identification', '=', 'TEST-UPDATED')]),
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                with self.assertRaises(AccessError), self.cr.savepoint():
                    operation()

    def test_buyer_cannot_import_nrc(self):
        result = self.env['res.partner'].with_user(self.buyer).load(
            ['id', 'name', 'hair_identification'],
            [['__import__.forbidden_seller', 'Forbidden seller', 'FORBIDDEN']],
        )
        self.assertTrue(result['messages'])
        self.assertTrue(any(message['type'] == 'error' for message in result['messages']))

    def test_unrelated_contact_permissions_do_not_grant_seller_management(self):
        Partner = self.env['res.partner'].with_user(self.contact_manager)
        with self.assertRaises(AccessError), self.cr.savepoint():
            Partner.create({'name': 'Forbidden', 'hair_is_seller': True, 'company_id': self.company.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.seller.with_user(self.contact_manager).write({'name': 'Forbidden'})
        contact = Partner.create({'name': 'Ordinary contact'})
        contact.write({'phone': 'TEST-PHONE'})
        self.assertEqual(contact.phone, 'TEST-PHONE')

    def test_cross_company_seller_protection(self):
        foreign = self.env['res.partner'].create({
            'name': 'Foreign Seller', 'hair_is_seller': True,
            'company_id': self.other_company.id,
        })
        Partner = self.env['res.partner'].with_user(self.buyer)
        self.assertFalse(Partner.search([('id', '=', foreign.id)]))
        operations = (
            lambda: foreign.with_user(self.buyer).read(['name']),
            lambda: foreign.with_user(self.buyer).write({'name': 'Forbidden'}),
            lambda: self.seller.with_user(self.buyer).write({'company_id': self.other_company.id}),
            lambda: Partner.create({'name': 'Forbidden', 'hair_is_seller': True, 'company_id': self.other_company.id}),
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                with self.assertRaises(AccessError), self.cr.savepoint():
                    operation()

    def test_company_and_type_integrity(self):
        other_type = self.env['hair.seller.type'].create({
            'name': 'Foreign Type', 'company_id': self.other_company.id,
        })
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.seller.write({'hair_seller_type_id': other_type.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.seller.write({'company_id': False})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.seller.write({'name': '   '})

    def test_buyer_seller_form_hides_identification(self):
        view = self.env['res.partner'].with_user(self.buyer).get_view(
            self.env.ref('base.view_partner_form').id, 'form',
        )
        self.assertNotIn('name="hair_identification"', view['arch'])
        view = self.env['res.partner'].with_user(self.manager).get_view(
            self.env.ref('base.view_partner_form').id, 'form',
        )
        self.assertIn('name="hair_identification"', view['arch'])
