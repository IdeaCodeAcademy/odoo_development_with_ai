from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestLocationSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Location company'})
        cls.user = new_test_user(cls.env, login='location_user')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Restricted location', 'company_id': cls.company.id,
        })

    def test_location_update_respects_company_rule(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['res.partner'].with_user(self.user).update_latitude_longitude([{
                'id': self.partner.id, 'partner_latitude': 16.8,
                'partner_longitude': 96.1,
            }])
        self.assertEqual(self.partner.partner_latitude, 0)

    def test_location_update_allowed_partner(self):
        partner = self.user.partner_id
        self.env['res.partner'].with_user(self.user).update_latitude_longitude([{
            'id': partner.id, 'partner_latitude': 16.8, 'partner_longitude': 96.1,
        }])
        self.assertAlmostEqual(partner.partner_latitude, 16.8)

    def test_user_can_update_own_theme(self):
        self.user.with_user(self.user).write({'color_scheme': 'dark'})
        self.assertEqual(self.user.color_scheme, 'dark')

    def test_user_cannot_update_another_users_theme(self):
        other = new_test_user(self.env, login='other_location_user')
        with self.assertRaises(AccessError), self.cr.savepoint():
            other.with_user(self.user).write({'color_scheme': 'dark'})

    def test_location_update_respects_partner_write_permission(self):
        partner = self.env['res.partner'].create({'name': 'Read-only partner'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['res.partner'].with_user(self.user).update_latitude_longitude([{
                'id': partner.id, 'partner_latitude': 16.8, 'partner_longitude': 96.1,
            }])
        self.assertEqual(partner.partner_latitude, 0)
