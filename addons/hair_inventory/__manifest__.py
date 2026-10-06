{
    'name': 'Hair Inventory',
    'version': '20.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Fully paid partial hair receipts and source lot traceability',
    'author': 'IdeaCode Academy',
    'license': 'LGPL-3',
    'depends': ['hair_purchase', 'stock'],
    'data': ['security/hair_inventory_security.xml', 'security/ir.access.csv',
             'views/hair_type_views.xml', 'views/hair_receipt_views.xml'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
