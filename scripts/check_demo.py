"""Check demo authentication and installed addons without displaying credentials."""
import json
import logging
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener

logging.basicConfig(level=logging.INFO, format='%(message)s')
_logger = logging.getLogger(__name__)

opener = build_opener(HTTPCookieProcessor(CookieJar()))
base_url = 'http://127.0.0.1:8071'


def rpc(path, params):
    payload = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params}).encode()
    request = Request(base_url + path, data=payload, headers={'Content-Type': 'application/json'})
    with opener.open(request, timeout=30) as response:
        result = json.load(response)
    if 'error' in result:
        raise RuntimeError('Demo RPC failed: ' + result['error'].get('message', 'unknown error'))
    return result['result']


credentials = Path('.demo_credentials').read_text(encoding='utf-8')
password = credentials.split('Password: ', 1)[1].strip()
session = rpc('/web/session/authenticate', {'db': 'hair_demo', 'login': 'admin', 'password': password})
assert session.get('uid'), 'Demo authentication failed'
modules = rpc('/web/session/modules', {})
assert {'hair_base', 'hair_supplier', 'hair_purchase', 'hair_inventory', 'ica_web_responsive'}.issubset(modules), 'Required addons not installed'
seller_count = rpc('/web/dataset/call_kw/res.partner/search_count', {
    'model': 'res.partner', 'method': 'search_count',
    'args': [[('hair_is_seller', '=', True)]], 'kwargs': {},
})
assert seller_count >= 1, 'Demo seller not found'
sellers = rpc('/web/dataset/call_kw/res.partner/search_read', {
    'model': 'res.partner', 'method': 'search_read',
    'args': [[('hair_is_seller', '=', True)]],
    'kwargs': {'fields': ['hair_intake_count', 'hair_intake_weight', 'hair_last_intake_date', 'hair_purchase_count', 'hair_purchase_weight', 'hair_purchase_value_summary', 'hair_last_purchase_date'], 'limit': 1},
})
assert sellers and sellers[0]['hair_intake_count'] >= 0, 'Intake history fields unavailable'
action = rpc('/web/dataset/call_kw/res.partner/action_view_hair_intakes', {
    'model': 'res.partner', 'method': 'action_view_hair_intakes', 'args': [[sellers[0]['id']]], 'kwargs': {},
})
assert action['domain'] == [['seller_id', '=', sellers[0]['id']]], 'Seller history filter incorrect'
purchase_action = rpc('/web/dataset/call_kw/res.partner/action_view_hair_purchases', {
    'model': 'res.partner', 'method': 'action_view_hair_purchases', 'args': [[sellers[0]['id']]], 'kwargs': {},
})
assert purchase_action['domain'] == [['seller_id', '=', sellers[0]['id']], ['state', 'in', ['confirmed', 'paid', 'received']]]
quality_fields = rpc('/web/dataset/call_kw/hair.purchase/fields_get', {
    'model': 'hair.purchase', 'method': 'fields_get', 'args': [['state', 'quality_approved', 'inspector_id', 'confirmed_currency_id', 'quoted_date', 'amount_total', 'paid_amount', 'balance_amount', 'payment_status']], 'kwargs': {},
})
assert {'draft', 'inspection', 'rejected', 'confirmed', 'cancelled', 'paid', 'received'}.issubset({key for key, _label in quality_fields['state']['selection']})
assert quality_fields['quality_approved']['readonly'], 'Quality approval metadata must be readonly'
assert quality_fields['confirmed_currency_id']['readonly'], 'Confirmed currency must be protected'
form = rpc('/web/dataset/call_kw/hair.purchase/get_view', {
    'model': 'hair.purchase', 'method': 'get_view', 'args': [], 'kwargs': {'view_type': 'form'},
})
assert 'action_confirm_purchase' in form['arch'], 'Commercial confirmation form unavailable'
assert 'action_quote_purchase' in form['arch'], 'Pricing review form unavailable'
assert 'action_open_price_override' in form['arch'], 'Price override form unavailable'
payment_form = rpc('/web/dataset/call_kw/hair.purchase.payment/get_view', {
    'model': 'hair.purchase.payment', 'method': 'get_view', 'args': [], 'kwargs': {'view_type': 'form'},
})
assert 'action_post' in payment_form['arch'], 'Payment posting form unavailable'
receipt_form = rpc('/web/dataset/call_kw/hair.receipt/get_view', {
    'model': 'hair.receipt', 'method': 'get_view', 'args': [], 'kwargs': {'view_type': 'form'},
})
assert 'action_receive' in receipt_form['arch'], 'Hair receipt form unavailable'
lot_form = rpc('/web/dataset/call_kw/stock.lot/get_view', {
    'model': 'stock.lot', 'method': 'get_view', 'args': [], 'kwargs': {'view_type': 'form'},
})
assert 'hair_receipt_line_id' in lot_form['arch'], 'Hair lot traceability form unavailable'
precision = rpc('/web/dataset/call_kw/decimal.precision/search_read', {
    'model': 'decimal.precision', 'method': 'search_read', 'args': [[('name', '=', 'Product Unit')]],
    'kwargs': {'fields': ['digits']},
})
assert precision and precision[0]['digits'] >= 3, 'Stock precision must preserve 0.001 kg'
user = rpc('/web/dataset/call_kw/res.users/read', {
    'model': 'res.users', 'method': 'read', 'args': [[session['uid']], ['company_id']], 'kwargs': {},
})[0]
company = rpc('/web/dataset/call_kw/res.company/read', {
    'model': 'res.company', 'method': 'read', 'args': [[user['company_id'][0]], ['currency_id']], 'kwargs': {},
})[0]
assert company['currency_id'][1] == 'MMK', 'Demo company currency must be MMK'
with opener.open(base_url + '/odoo', timeout=30) as response:
    assert response.status == 200
_logger.info('Demo authentication, installed addons and web page checks passed')

reports = rpc('/web/dataset/call_kw/ir.actions.report/search_read', {
    'model': 'ir.actions.report', 'method': 'search_read',
    'args': [[('report_name', '=', 'hair_purchase.purchase_receipt')]],
    'kwargs': {'fields': ['report_type', 'binding_model_id', 'group_ids']},
})
assert len(reports) == 1 and reports[0]['report_type'] == 'qweb-pdf', 'Purchase PDF receipt unavailable'
assert reports[0]['binding_model_id'] and reports[0]['group_ids'], 'Receipt binding/security unavailable'
_logger.info('Purchase receipt report registration passed')

search_view = rpc('/web/dataset/call_kw/hair.purchase/get_view', {
    'model': 'hair.purchase', 'method': 'get_view', 'args': [], 'kwargs': {'view_type': 'search'},
})
assert all(token in search_view['arch'] for token in ('Seller Phone', 'Hair Type', 'Grade', 'Length', 'commercial_purchases', 'outstanding_payments', 'group_payment')), 'Purchase search filters unavailable'
_logger.info('Purchase search view passed')
