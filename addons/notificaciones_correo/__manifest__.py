# -*- coding: utf-8 -*-
{
    'name': "notificaciones_correo",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','mail','stock','hr','account_invoicing'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/email_template.xml',
        'data/nopaid_mail_cron.xml',
        'data/nogiveback_mail_cron.xml',
    ],
}