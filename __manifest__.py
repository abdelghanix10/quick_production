{
    'name': 'Quick Production',
    'version': '20.0.2.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Simplified Kiosk production interface for manufacturing staff',
    'description': """
Quick Production (Odoo 20)
==========================
Provides a simplified Kiosk Mode interface for operators to register production quickly:
- Kanban dashboard filtered by user's assigned Production Categories.
- Quick Production Wizard with touchscreen quantity buttons (+1, +5, +10, +50).
- Automatic BOM explosion with real-time ingredient stock availability check.
- One-click Immediate Production (Done) or Queue Production (Pending).
- Bulk Pending Production manager with partial backorder support.
    """,
    'depends': ['mrp', 'stock', 'product'],
    'data': [
        'security/ir.access.csv',
        'views/dashboard_action.xml',
        'views/wizard_view.xml',
        'views/bulk_production_view.xml',
        'views/res_users_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}