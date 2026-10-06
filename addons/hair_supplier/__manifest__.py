{
    'name': 'Hair Seller Management',
    'version': '20.0.1.0.0',
    'category': 'Purchases',
    'author': 'IdeaCode Academy',
    'license': 'LGPL-3',
    'depends': ['hair_base', 'contacts'],
    'data': [
        'security/hair_supplier_groups.xml',
        'security/ir.access.csv',
        'security/hair_supplier_security.xml',
        'views/hair_seller_type_views.xml',
        'views/res_partner_views.xml',
    ],
    'demo': ['demo/hair_supplier_demo.xml'],
    'installable': True,
}
