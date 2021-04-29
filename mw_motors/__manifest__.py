# -*- coding: utf-8 -*-

{
    'name': 'DMS Management',
    'version': '1.0',
    'sequence': 11,
    'category': 'Repair',
    'website': 'http://manangewall.mn',
    'author': 'Amaraa',
    'description': """
        Car repair and maintenance """,
    'depends': ['base','mail','stock','web_widget_colorpicker','branch','web_widget_image_webcam',
                'wk_product_pack','web_digital_sign','mw_send_chat'],
    'summary': '',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/car_setting_view.xml',
        'views/car_view.xml',
        'views/car_inspection_view.xml',
        'views/car_diagnosis_view.xml',

        'views/car_repair_order_view.xml',
        'views/repairman_repair_order_view.xml',
        'views/maintenance_settings_view.xml',

        'views/res_partner_inherit_view.xml',
        'views/stock_picking_inherit_view.xml',

        'views/car_forecast_generator_view.xml',

        'reports/car_inspection_pivot_report_view.xml',
        'reports/car_forecast_pivot_report_view.xml',

        'boards/stall_order_setting_view.xml',
        'boards/appointment_scheduling_board_view.xml',
        'boards/job_planning_board_view.xml',
        'boards/appointment_preparation_board_view.xml',
        'boards/job_progress_control_board_view.xml',

        'views/widget_path.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/*.xml'],
}
