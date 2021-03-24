{
    # Theme information

    'name': 'Mw auction',
    'category': 'Theme/eCommerce',
    'summary': 'MW ecomerce.',
    'version': '1.0.0',
    'license': 'OPL-1',
    'depends': [
        'website_theme_install',
        'website_sale_wishlist',
        'website_sale_stock',
        'website_sale',
        'auth_signup',
        'emipro_theme_base',
        'theme_clarico_vega',
        'portal',
        'crm',
        'website_auction',
        'website_sale_wishlist'
    ],
    'data': [
        'security/ir.model.access.csv',
        'templates/shop.xml',
        'templates/assets.xml',
        'views/auction_view.xml',
        'views/res_users_view.xml',
        'templates/auth_signup_login_templates.xml',
        "views/cron.xml"
    ],

    'images': [
    ],

    # Author
    'author': 'Managewall',
    'website': 'www.managewall.mn',
    'maintainer': 'Daramaa',

    # Technical
    'installable': True,
    'auto_install': False,
}
