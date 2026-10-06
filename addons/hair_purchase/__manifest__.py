{
    'name': 'Hair Purchase Intake',
    'version': '20.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Company-scoped draft hair intake and kilogram weights',
    'author': 'IdeaCode Academy',
    'license': 'LGPL-3',
    'depends': ['hair_supplier', 'mail'],
    'data': [
        'security/ir.access.csv',
        'security/hair_purchase_security.xml',
        'data/hair_purchase_data.xml',
        'views/hair_purchase_views.xml',
        'views/hair_pricing_rule_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
}
