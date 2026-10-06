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
assert {'hair_base', 'hair_supplier', 'hair_purchase', 'ica_web_responsive'}.issubset(modules), 'Required addons not installed'
seller_count = rpc('/web/dataset/call_kw/res.partner/search_count', {
    'model': 'res.partner', 'method': 'search_count',
    'args': [[('hair_is_seller', '=', True)]], 'kwargs': {},
})
assert seller_count >= 1, 'Demo seller not found'
sellers = rpc('/web/dataset/call_kw/res.partner/search_read', {
    'model': 'res.partner', 'method': 'search_read',
    'args': [[('hair_is_seller', '=', True)]],
    'kwargs': {'fields': ['hair_intake_count', 'hair_intake_weight', 'hair_last_intake_date'], 'limit': 1},
})
assert sellers and sellers[0]['hair_intake_count'] >= 0, 'Intake history fields unavailable'
action = rpc('/web/dataset/call_kw/res.partner/action_view_hair_intakes', {
    'model': 'res.partner', 'method': 'action_view_hair_intakes', 'args': [[sellers[0]['id']]], 'kwargs': {},
})
assert action['domain'] == [['seller_id', '=', sellers[0]['id']]], 'Seller history filter incorrect'
quality_fields = rpc('/web/dataset/call_kw/hair.purchase/fields_get', {
    'model': 'hair.purchase', 'method': 'fields_get', 'args': [['state', 'quality_approved', 'inspector_id']], 'kwargs': {},
})
assert {'draft', 'inspection', 'rejected'}.issubset({key for key, _label in quality_fields['state']['selection']})
assert quality_fields['quality_approved']['readonly'], 'Quality approval metadata must be readonly'
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
