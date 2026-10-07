import io

from PIL import Image

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairMasterData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Other Hair Company'})
        cls.reader = new_test_user(
            cls.env, login='hair_reader', groups='hair_base.hair_base_group_user',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.manager = new_test_user(
            cls.env, login='hair_config', groups='hair_base.hair_base_group_manager',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
        )
        cls.outsider = new_test_user(cls.env, login='hair_outsider')
        cls.portal = new_test_user(cls.env, login='hair_portal', groups='base.group_portal')
        cls.models = ('hair.type', 'hair.texture', 'hair.color', 'hair.grade', 'hair.length')

    def test_configuration_creation_and_archiving(self):
        for model in self.models:
            with self.subTest(model=model):
                Model = self.env[model].with_user(self.manager)
                record = Model.create({'name': 'Custom Configuration'})
                self.assertEqual(record.company_id, self.company)
                record.with_user(self.reader).read(['name'])
                record.write({'name': 'Renamed Configuration', 'active': False})
                self.assertFalse(Model.search([('id', '=', record.id)]))
                self.assertEqual(
                    Model.with_context(active_test=False).search([('id', '=', record.id)]), record,
                )

    def test_reader_cannot_mutate_configuration(self):
        for model in self.models:
            with self.subTest(model=model):
                record = self.env[model].create({'name': 'Protected Configuration'})
                for operation in (
                    lambda: self.env[model].with_user(self.reader).create({'name': 'Unauthorized'}),
                    lambda: record.with_user(self.reader).write({'name': 'Unauthorized'}),
                    lambda: record.with_user(self.reader).unlink(),
                    lambda: record.with_user(self.manager).unlink(),
                ):
                    with self.assertRaises(AccessError), self.cr.savepoint():
                        operation()

    def test_no_access_without_hair_role(self):
        for model in self.models:
            for user in (self.outsider, self.portal, self.env.ref('base.public_user')):
                with self.subTest(model=model, user=user.login):
                    with self.assertRaises(AccessError), self.cr.savepoint():
                        self.env[model].with_user(user).search([])

    def test_company_isolation_read_create_write(self):
        for model in self.models:
            with self.subTest(model=model):
                other = self.env[model].create({
                    'name': 'Other Company', 'company_id': self.other_company.id,
                })
                own = self.env[model].with_user(self.manager).create({'name': 'Own Company'})
                Model = self.env[model].with_user(self.manager)
                self.assertFalse(Model.search([('id', '=', other.id)]))
                operations = (
                    lambda: other.with_user(self.reader).read(['name']),
                    lambda: other.with_user(self.manager).write({'name': 'Forbidden'}),
                    lambda: own.write({'company_id': self.other_company.id}),
                    lambda: Model.create({'name': 'Forbidden', 'company_id': self.other_company.id}),
                )
                for index, operation in enumerate(operations):
                    with self.subTest(operation=index):
                        with self.assertRaises(AccessError), self.cr.savepoint():
                            operation()
                with self.assertRaises(AccessError), self.cr.savepoint():
                    Model.with_context(allowed_company_ids=self.other_company.ids).search([])

    def test_blank_names_rejected(self):
        for model in self.models:
            with self.subTest(model=model):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    self.env[model].create({'name': '   '})

    def test_length_exact_range_and_open_upper_bound(self):
        Length = self.env['hair.length'].with_user(self.manager)
        exact = Length.create({'name': 'Exact', 'length_min': 12, 'length_max': 12})
        bounded = Length.create({'name': 'Range', 'length_min': 10, 'length_max': 14})
        upper_open = Length.create({'name': 'Long', 'length_min': 27, 'open_ended': True})
        self.assertEqual(exact.length_min, exact.length_max)
        self.assertGreater(bounded.length_max, bounded.length_min)
        self.assertTrue(upper_open.open_ended)

    def test_invalid_length_bounds_create_and_write(self):
        Length = self.env['hair.length'].with_user(self.manager)
        invalid_values = (
            {'length_min': -1}, {'length_max': -1},
            {'length_min': 15, 'length_max': 10},
            {'length_min': float('inf')}, {'length_max': float('inf')},
        )
        record = Length.create({'name': 'Valid', 'length_min': 10, 'length_max': 14})
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    Length.create(dict(values, name='Invalid'))
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    record.write(values)

    def test_all_configuration_actions_have_views(self):
        for model in self.models:
            action = self.env.ref('hair_base.' + model.replace('.', '_') + '_action')
            self.assertEqual(action.res_model, model)
            self.env[model].with_user(self.reader).get_views(
                [(False, 'list'), (False, 'form'), (False, 'search')], {},
            )

    def test_application_menu_icon_loads(self):
        menu = self.env.ref('hair_base.hair_base_menu_root')
        self.assertEqual(menu.web_icon, 'hair_base,static/description/icon.png')
        self.assertTrue(menu.web_icon_data)
        with Image.open(io.BytesIO(bytes(menu.web_icon_data))) as icon:
            self.assertEqual(icon.format, 'PNG')
            self.assertEqual(icon.size, (256, 256))
