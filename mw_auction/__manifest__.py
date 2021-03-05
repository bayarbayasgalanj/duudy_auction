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
    ],

    'data': [
        'templates/shop.xml',
        'templates/assets.xml',
        'views/auction_view.xml'
    ],

    'images': [
        'static/description/main_poster.jpg',
        'static/description/main_screenshot.gif',
    ],

    # Author
    'author': 'Managewall',
    'website': 'www.managewall.mn',
    'maintainer': 'Daramaa',

    # Technical
    'installable': True,
    'auto_install': False,
}
