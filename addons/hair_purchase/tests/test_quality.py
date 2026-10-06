from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairQuality(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.buyer = new_test_user(cls.env, login='quality_buyer', groups='hair_supplier.hair_supplier_group_buyer',
                                 company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.officer = new_test_user(cls.env, login='quality_officer', groups='hair_purchase.hair_purchase_group_quality',
                                   company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.seller = cls.env['res.partner'].create({'name': 'Quality Seller', 'hair_is_seller': True, 'company_id': cls.company.id})
        cls.hair_type = cls.env['hair.type'].create({'name': 'Quality Type'})
        cls.length = cls.env['hair.length'].create({'name': 'Quality Length', 'length_min': 12, 'length_max': 12})
        cls.grade = cls.env['hair.grade'].create({'name': 'Approved Quality Grade'})
        cls.Purchase = cls.env['hair.purchase'].with_user(cls.buyer)

    def intake(self):
        return self.Purchase.create({'seller_id': self.seller.id, 'line_ids': [Command.create({
            'hair_type_id': self.hair_type.id, 'length_id': self.length.id, 'gross_weight': 1,
        })]})

    def inspected(self):
        purchase = self.intake()
        purchase.action_submit_inspection()
        return purchase

    def test_submit_requires_complete_lines_and_is_retry_safe(self):
        empty = self.Purchase.create({'seller_id': self.seller.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            empty.action_submit_inspection()
        purchase = self.intake()
        for field, value in (('hair_type_id', False), ('length_id', False), ('gross_weight', 0)):
            with self.cr.savepoint():
                original = purchase.line_ids[field]
                purchase.line_ids.write({field: value})
                with self.assertRaises(ValidationError):
                    purchase.action_submit_inspection()
                purchase.line_ids.write({field: original.id if field.endswith('_id') else original})
        purchase.action_submit_inspection()
        purchase.action_submit_inspection()
        self.assertEqual(purchase.state, 'inspection')
        self.assertFalse(purchase.quality_approved)

    def test_grade_approval_and_return_to_draft_invalidate_approval(self):
        purchase = self.inspected()
        officer_purchase = purchase.with_user(self.officer)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            officer_purchase.action_approve_quality()
        officer_purchase.line_ids.write({'proposed_grade_id': self.grade.id})
        officer_purchase.write({'inspection_notes': 'Inspection evidence recorded'})
        officer_purchase.action_approve_quality()
        date = officer_purchase.inspection_date
        officer_purchase.action_approve_quality()
        self.assertTrue(purchase.quality_approved)
        self.assertEqual(purchase.line_ids.grade_id, self.grade)
        self.assertEqual(purchase.inspector_id, self.officer)
        self.assertEqual(purchase.inspection_date, date)
        duplicate = purchase.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.quality_approved)
        self.assertFalse(duplicate.inspector_id)
        self.assertFalse(duplicate.inspection_notes)
        self.assertFalse(duplicate.line_ids.grade_id)
        self.assertFalse(duplicate.line_ids.proposed_grade_id)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_return_to_draft()
        purchase.write({'revision_reason': 'Correct measured kg'})
        purchase.action_return_to_draft()
        self.assertTrue(any('Correct measured kg' in str(message.body) and self.grade.name in str(message.body) for message in purchase.message_ids))
        self.assertEqual(purchase.state, 'draft')
        self.assertFalse(purchase.quality_approved)
        self.assertFalse(purchase.inspector_id)
        self.assertFalse(purchase.line_ids.grade_id)
        self.assertFalse(purchase.line_ids.proposed_grade_id)
        purchase.line_ids.write({'gross_weight': 2})
        purchase.action_submit_inspection()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            officer_purchase.action_approve_quality()

    def test_role_permissions_do_not_grant_buyer_or_nrc_access(self):
        purchase = self.inspected()
        for action in (purchase.action_approve_quality, purchase.action_reject_quality):
            with self.assertRaises(AccessError), self.cr.savepoint():
                action()
        with self.assertRaises(AccessError), self.cr.savepoint():
            purchase.line_ids.write({'proposed_grade_id': self.grade.id})
        officer_purchase = purchase.with_user(self.officer)
        self.assertEqual(officer_purchase.seller_id.name, 'Quality Seller')
        form = self.env.ref('hair_purchase.hair_purchase_view_form')
        self.assertNotIn('action_approve_quality', self.Purchase.get_view(form.id, 'form')['arch'])
        self.assertIn('action_approve_quality', officer_purchase.get_view(form.id, 'form')['arch'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            officer_purchase.action_return_to_draft()
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['hair.purchase'].with_user(self.officer).create({'seller_id': self.seller.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.seller.with_user(self.officer).write({'name': 'Forbidden'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.seller.with_user(self.officer).read(['hair_identification'])

    def test_inspected_intake_inputs_and_line_membership_are_locked(self):
        purchase = self.inspected()
        draft = self.intake()
        operations = (
            lambda: purchase.write({'seller_id': self.seller.id}),
            lambda: purchase.line_ids.write({'gross_weight': 2}),
            lambda: purchase.line_ids.write({'purchase_id': draft.id}),
            purchase.line_ids.unlink,
            lambda: self.env['hair.purchase.line'].with_user(self.buyer).create({'purchase_id': purchase.id}),
            lambda: purchase.write({'line_ids': [Command.link(draft.line_ids.id)]}),
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    operation()

    def test_rejection_requires_reason_and_is_terminal(self):
        purchase = self.inspected().with_user(self.officer)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_reject_quality()
        purchase.write({'rejection_reason': '   '})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.action_reject_quality()
        purchase.write({'rejection_reason': 'Rejected after inspection'})
        purchase.action_reject_quality()
        self.assertEqual(purchase.state, 'rejected')
        self.assertEqual(purchase.inspector_id, self.officer)
        self.assertTrue(purchase.inspection_date)
        self.assertFalse(purchase.quality_approved)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.with_user(self.buyer).action_return_to_draft()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.with_user(self.buyer).action_submit_inspection()

    def test_direct_metadata_and_context_forgery_is_blocked(self):
        purchase = self.intake()
        for vals in ({'quality_approved': True}, {'inspector_id': self.officer.id}, {'inspection_date': '2026-01-01'}, {'state': 'inspection'}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                purchase.write(vals)
            if 'state' not in vals:
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    self.Purchase.create({'seller_id': self.seller.id, **vals})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.line_ids.write({'grade_id': self.grade.id})
        forged = self.Purchase.with_context(default_state='inspection', default_quality_approved=True, default_inspector_id=self.officer.id).create({'seller_id': self.seller.id})
        self.assertEqual(forged.state, 'draft')
        self.assertFalse(forged.quality_approved)
        self.assertFalse(forged.inspector_id)
        purchase.action_submit_inspection()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            purchase.with_context(hair_workflow=True).write({'state': 'draft'})

    def test_grade_company_integrity_and_foreign_actions(self):
        purchase = self.inspected().with_user(self.officer)
        company = self.env['res.company'].create({'name': 'Foreign Quality Company'})
        grade = self.env['hair.grade'].create({'name': 'Foreign Grade', 'company_id': company.id})
        with self.assertRaises(UserError), self.cr.savepoint():
            purchase.line_ids.write({'proposed_grade_id': grade.id})
        seller = self.env['res.partner'].create({'name': 'Foreign Seller', 'hair_is_seller': True, 'company_id': company.id})
        foreign = self.env['hair.purchase'].create({'seller_id': seller.id, 'company_id': company.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            foreign.with_user(self.officer).action_approve_quality()

    def test_approved_inspection_findings_are_protected(self):
        purchase = self.inspected().with_user(self.officer)
        purchase.line_ids.write({'proposed_grade_id': self.grade.id})
        purchase.action_approve_quality()
        operations = (
            lambda: purchase.write({'inspection_notes': 'Changed'}),
            lambda: purchase.line_ids.write({'proposed_grade_id': False}),
            purchase.action_reject_quality,
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    operation()
