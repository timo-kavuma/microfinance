# -*- coding: utf-8 -*-
{
    'name': "See Resolved Queries",

    'summary': """
        See resolved queries made to postgresql to measure performance.""",

    'description': """
        See resolved queries made to postgresql to measure performance.
    """,

    'author': "JUVENTUD PRODUCTIVA VENEZOLANA",
    'website': "http://www.juventudproductivabicentenaria.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tool',
    'version': '0.1',
    'license': 'AGPL-3',
    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/query_security.xml',
        'views/resolved_queries.xml',
        'wizard/run_resolved_queries.xml',
        'wizard/data_resolved_queries.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/images/resolved_queries_screenshot.gif'],
}
