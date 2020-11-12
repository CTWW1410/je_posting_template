# -*- coding: utf-8 -*-
##############################################################################
# Odoo Additional Function by CTWW
##############################################################################
{
    'name': "JE Posting Template",

    'summary': """
        Utility to help user can faster input Journal Entry""",

    'description': """
        You can declare JE templates with this module, and reuse it at Journal Entry.
    """,

    'author': "CTWW",
    'website': "https://www.linkedin.com/in/ngo-manh-70a68b183/",
    'category': 'Account',
    'version': '12.0.1.0.1',
    'depends': ['base', 'mail', 'account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/posting_template.xml',
        'views/account_move.xml',
    ],
    'demo': [
    ],
    'images': ['static/description/main_screenshot.png'],

}