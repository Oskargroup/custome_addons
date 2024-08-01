# -*- coding: utf-8 -*-
{
    'name': "project_ext",

    'summary': """
        Add some extra features and access rights to default project module""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OGroup",


    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'portal'],

    # always loaded
    'data': [
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/project.xml',
        'views/project_task.xml',
        'views/project_report.xml',
        'views/portal_templates.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'project_ext/static/src/js/project_task_kanban_header.js'
        ]
    }
}
