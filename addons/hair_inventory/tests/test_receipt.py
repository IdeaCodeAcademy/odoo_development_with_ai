from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHairReceipt(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.buyer = new_test_user(cls.env, login='receipt_buyer', groups='hair_supplier.hair_supplier_group_buyer')
        cls.manager = new_test_user(cls.env, login='receipt_manager', groups='hair_supplier.hair_supplier_group_manager')
        cls.officer = new_test_user(cls.env, login='receipt_officer', groups='hair_purchase.hair_purchase_group_quality')
        cls.cashier = new_test_user(cls.env, login='receipt_cashier', groups='hair_purchase.hair_purchase_group_cashier')
        cls.warehouse = new_test_user(cls.env, login='receipt_warehouse', groups='hair_inventory.group_hair_warehouse')
        cls.product = cls.env['product.product'].create({'name': 'Receipt Hair', 'is_storable': True,
                                                       'tracking': 'lot', 'uom_id': cls.env.ref('uom.product_uom_kgm').id})
        cls.hair_type = cls.env['hair.type'].create({'name': 'Receipt Type', 'stock_product_id': cls.product.id})
        cls.grade = cls.env['hair.grade'].create({'name': 'Receipt Grade'})
        cls.length = cls.env['hair.length'].create({'name': 'Receipt Length', 'length_min': 12, 'length_max': 14})
        cls.seller = cls.env['res.partner'].create({'name': 'Original Receipt Seller', 'hair_is_seller': True, 'company_id': cls.env.company.id})
        cls.method = cls.env['hair.payment.method'].create({'name': 'Synthetic Receipt Payment'})
        cls.rule = cls.env['hair.pricing.rule'].create({'name': 'Synthetic Receipt Price', 'hair_type_id': cls.hair_type.id,
                                                      'grade_id': cls.grade.id, 'length_id': cls.length.id,
                                                      'price_per_kg': 100, 'date_start': '2026-01-01'})
        cls.operation = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1).in_type_id

    def purchase(self, paid=True, line_count=1):
        purchase = self.env['hair.purchase'].with_user(self.buyer).create({
            'seller_id': self.seller.id, 'date': '2026-01-02 10:00:00',
            'line_ids': [Command.create({'hair_type_id': self.hair_type.id, 'length_id': self.length.id, 'gross_weight': .601}) for _line in range(line_count)],
        })
        purchase.action_submit_inspection()
        purchase.with_user(self.officer).line_ids.write({'proposed_grade_id': self.grade.id})
        purchase.with_user(self.officer).action_approve_quality()
        purchase.with_user(self.manager).action_quote_purchase()
        purchase.with_user(self.manager).action_confirm_purchase()
        if paid:
            self.env['hair.purchase.payment'].with_user(self.cashier).create({
                'purchase_id': purchase.id, 'method_id': self.method.id, 'amount': purchase.amount_total,
            }).action_post()
        return purchase

    def receipt(self, purchase, quantity):
        return self.env['hair.receipt'].with_user(self.warehouse).create({
            'purchase_id': purchase.id, 'picking_type_id': self.operation.id,
            'line_ids': [Command.create({'purchase_line_id': purchase.line_ids.id, 'quantity': quantity})],
        })

    def test_partial_full_receipt_lots_and_retries(self):
        purchase = self.purchase()
        first = self.receipt(purchase, .3)
        first.with_context(default_state='done', default_hair_receipt_id=999, default_return_id=999).action_receive()
        self.assertEqual(first.picking_id.state, 'done')
        self.assertEqual(purchase.state, 'paid')
        self.assertAlmostEqual(purchase.line_ids.received_weight, .3)
        picking = first.picking_id
        first.action_receive()
        self.assertEqual(first.picking_id, picking)
        second = self.receipt(purchase, .301)
        second.action_receive()
        self.assertEqual(purchase.state, 'received')
        self.assertAlmostEqual(purchase.line_ids.received_weight, .601)
        self.assertEqual(self.seller.with_user(self.buyer).hair_purchase_count, 1)
        lot = second.picking_id.move_ids.move_line_ids.lot_id
        self.assertEqual(lot.hair_purchase_id, purchase.with_user(self.warehouse))
        self.assertEqual(lot.hair_original_weight, .301)
        self.seller.name = 'Changed Seller'
        self.assertEqual(lot.hair_seller_snapshot, 'Original Receipt Seller')
        quants = self.env['stock.quant'].search([('product_id', '=', self.product.id), ('location_id', '=', picking.location_dest_id.id)])
        self.assertAlmostEqual(sum(quants.mapped('quantity')), .601)

    def test_payment_prerequisite_and_quantity_limits(self):
        unpaid = self.purchase(paid=False)
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.receipt(unpaid, .1)
        purchase = self.purchase()
        for quantity in (0, -1, float('inf'), .0001):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.receipt(purchase, quantity)
        first = self.receipt(purchase, .4)
        second = self.receipt(purchase, .3)
        first.action_receive()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            second.action_receive()
        self.assertFalse(second.picking_id)
        self.assertEqual(second.state, 'draft')

    def test_receipt_roles_and_forged_provenance(self):
        purchase = self.purchase()
        receipt = self.receipt(purchase, .1)
        for user in (self.buyer, self.cashier, self.officer, self.manager, self.env.ref('base.public_user')):
            with self.assertRaises(AccessError), self.cr.savepoint():
                receipt.with_user(user).action_receive()
        for values in ({'state': 'done'}, {'picking_id': 1}, {'received_by_id': self.warehouse.id}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                receipt.write(values)
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.seller.with_user(self.warehouse).read(['hair_identification'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            purchase.with_user(self.warehouse).line_ids.write({'gross_weight': 3})
        self.assertIn('action_receive', str(receipt.get_view(view_type='form')['arch']))

    def test_completed_receipt_stock_and_lot_immutable(self):
        receipt = self.receipt(self.purchase(), .601)
        receipt.action_receive()
        move = receipt.picking_id.move_ids
        detail = move.move_line_ids
        for operation in (lambda: receipt.write({'picking_type_id': self.operation.id}), receipt.unlink,
                          lambda: receipt.line_ids.write({'quantity': .1}),
                          lambda: move.write({'quantity': .1}), lambda: detail.write({'quantity': .1}), detail.unlink,
                          lambda: detail.lot_id.write({'hair_receipt_line_id': False}), receipt.picking_id._create_return,
                          lambda: self.env['stock.picking'].with_user(self.warehouse).with_context(default_return_id=receipt.picking_id.id).create({}),
                          lambda: self.env['stock.move'].with_user(self.warehouse).with_context(default_origin_returned_move_id=move.id).create({})):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                operation()

    def test_direct_stock_link_forgery_blocked(self):
        receipt = self.receipt(self.purchase(), .1)
        for model, values in (
            ('stock.picking', {'hair_receipt_id': receipt.id}),
            ('stock.move', {'hair_receipt_line_id': receipt.line_ids.id}),
            ('stock.lot', {'hair_receipt_line_id': receipt.line_ids.id}),
        ):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.env[model].with_user(self.warehouse).create(values)
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.env[model].with_user(self.warehouse).with_context(**{f'default_{next(iter(values))}': next(iter(values.values()))}).create({})

    def test_wrong_source_line_and_operation(self):
        first, second = self.purchase(), self.purchase()
        receipt = self.receipt(first, .1)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            receipt.line_ids.write({'purchase_line_id': second.line_ids.id})
        outgoing = self.operation.warehouse_id.out_type_id
        with self.assertRaises(ValidationError), self.cr.savepoint():
            receipt.write({'picking_type_id': outgoing.id})

    def test_missing_configuration_is_atomic_and_foreign_access_denied(self):
        purchase = self.purchase()
        receipt = self.receipt(purchase, .1)
        self.hair_type.stock_product_id = False
        with self.assertRaises(ValidationError), self.cr.savepoint():
            receipt.action_receive()
        self.assertFalse(receipt.picking_id)
        self.assertEqual(receipt.state, 'draft')
        self.assertEqual(purchase.line_ids.received_weight, 0)
        company = self.env['res.company'].create({'name': 'Foreign Receipt Company'})
        seller = self.env['res.partner'].create({'name': 'Foreign Receipt Seller', 'hair_is_seller': True, 'company_id': company.id})
        foreign = self.env['hair.purchase'].create({'seller_id': seller.id, 'company_id': company.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['hair.receipt'].with_user(self.warehouse).create({'purchase_id': foreign.id, 'picking_type_id': self.operation.id})

    def test_completed_transfer_cannot_gain_stock_moves_or_details(self):
        receipt = self.receipt(self.purchase(), .601)
        receipt.action_receive()
        move = receipt.picking_id.move_ids
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['stock.move'].with_user(self.warehouse).create({'picking_id': receipt.picking_id.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['stock.move.line'].with_user(self.warehouse).create({'move_id': move.id, 'quantity': .1})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['stock.move.line'].with_user(self.warehouse).create({
                'product_id': self.product.id, 'company_id': self.env.company.id, 'lot_id': move.move_line_ids.lot_id.id,
                'uom_id': self.product.uom_id.id, 'quantity': .1,
                'location_id': receipt.picking_id.location_id.id,
                'location_dest_id': receipt.picking_id.location_dest_id.id,
            })
        self.assertEqual(receipt.purchase_id.with_user(self.cashier).payment_status, 'paid')

    def test_received_state_requires_every_purchase_line(self):
        purchase = self.purchase(line_count=2)
        for index, source in enumerate(purchase.line_ids):
            receipt = self.env['hair.receipt'].with_user(self.warehouse).create({
                'purchase_id': purchase.id, 'picking_type_id': self.operation.id,
                'line_ids': [Command.create({'purchase_line_id': source.id, 'quantity': .601})],
            })
            receipt.action_receive()
            self.assertEqual(purchase.state, 'paid' if index == 0 else 'received')
        self.assertAlmostEqual(sum(purchase.line_ids.mapped('received_weight')), 1.202)

    def test_partial_receipts_preserve_original_product(self):
        purchase = self.purchase()
        first = self.receipt(purchase, .3)
        first.action_receive()
        replacement = self.env['product.product'].create({'name': 'Changed Mapping Product', 'is_storable': True,
                                                         'tracking': 'lot', 'uom_id': self.product.uom_id.id})
        self.hair_type.stock_product_id = replacement
        second = self.receipt(purchase, .301)
        second.action_receive()
        self.assertEqual(second.picking_id.move_ids.product_id, self.product.with_user(self.warehouse))
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.product.write({'tracking': 'serial'})
