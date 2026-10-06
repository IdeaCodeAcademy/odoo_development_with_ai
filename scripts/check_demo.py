"""Check demo authentication and installed addons without displaying credentials."""
from http.cookiejar import CookieJar
import json
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener


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


credentials = Path('.demo_credentials').read_text()
password = credentials.split('Password: ', 1)[1].strip()
session = rpc('/web/session/authenticate', {'db': 'hair_demo', 'login': 'admin', 'password': password})
assert session.get('uid'), 'Demo authentication failed'
modules = rpc('/web/session/modules', {})
assert {'hair_base', 'hair_supplier', 'ica_web_responsive'}.issubset(modules), 'Required addons not installed'
seller_count = rpc('/web/dataset/call_kw/res.partner/search_count', {
    'model': 'res.partner', 'method': 'search_count',
    'args': [[('hair_is_seller', '=', True)]], 'kwargs': {},
})
assert seller_count >= 1, 'Demo seller not found'
with opener.open(base_url + '/odoo', timeout=30) as response:
    assert response.status == 200
print('Demo authentication, installed addons and web page checks passed')
