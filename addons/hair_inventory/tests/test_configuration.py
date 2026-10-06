from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairInventoryConfiguration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kg = cls.env.ref('uom.product_uom_kgm')
        cls.product = cls.env['product.product'].create({'name': 'Synthetic Hair Stock', 'is_storable': True,
                                                       'tracking': 'lot', 'uom_id': cls.kg.id})
        cls.hair_type = cls.env['hair.type'].create({'name': 'Inventory Type'})
        cls.reader = new_test_user(cls.env, login='inventory_config_reader', groups='hair_base.hair_base_group_user')
        cls.manager = new_test_user(cls.env, login='inventory_config_manager', groups='hair_base.hair_base_group_manager')

    def test_product_mapping_and_missing_configuration(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.hair_type._inventory_product()
        self.hair_type.with_user(self.manager).write({'stock_product_id': self.product.id})
        self.assertEqual(self.hair_type.with_user(self.reader)._inventory_product(), self.product.with_user(self.reader))
        self.assertIn('stock_product_id', str(self.hair_type.get_view(view_type='form')['arch']))

    def test_invalid_product_tracking_and_units(self):
        for values in ({'is_storable': False, 'tracking': False}, {'tracking': 'serial'},
                       {'uom_id': self.env.ref('uom.product_uom_unit').id}):
            with self.subTest(values=values), self.cr.savepoint():
                self.product.write(values)
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    self.hair_type.write({'stock_product_id': self.product.id})
                self.product.write({'is_storable': True, 'tracking': 'lot', 'uom_id': self.kg.id})

    def test_product_changes_cannot_invalidate_mapping(self):
        self.hair_type.stock_product_id = self.product
        for values in ({'tracking': False}, {'uom_id': self.env.ref('uom.product_uom_unit').id},
                       {'is_storable': False}, {'store_by': 'serial'}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.product.write(values)
        self.assertEqual(self.product.tracking, 'lot')
        self.hair_type.active = False
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.product.write({'tracking': 'serial'})
        self.hair_type.active = True
        self.product.active = False
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.hair_type._inventory_product()

    def test_mapping_permissions_and_public_access(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.hair_type.with_user(self.reader).write({'stock_product_id': self.product.id})
        self.hair_type.with_user(self.manager).stock_product_id = self.product
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.hair_type.with_user(self.env.ref('base.public_user'))._inventory_product()

    def test_foreign_company_product_and_type_denied(self):
        company = self.env['res.company'].create({'name': 'Foreign Inventory Company'})
        foreign_product = self.env['product.product'].create({'name': 'Foreign Hair', 'company_id': company.id,
                                                            'is_storable': True, 'tracking': 'lot', 'uom_id': self.kg.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.hair_type.write({'stock_product_id': foreign_product.id})
        foreign_type = self.env['hair.type'].create({'name': 'Foreign Type', 'company_id': company.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            foreign_type.with_user(self.manager).write({'stock_product_id': self.product.id})
