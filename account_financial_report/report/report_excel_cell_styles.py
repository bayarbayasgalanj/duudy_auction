# -*- coding: utf-8 -*-


class ReportExcelCellStyles:
    """xlsxwriter-т зориулсан форматууд
    """
    format_name = {
        'font_name': 'Times New Roman',
        'font_size': 16,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter'
    }

    format_date = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter'
    }

    format_filter = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter'
    }

    format_filter_right = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter'
    }

    format_title = {
        'font_name': 'Times New Roman',
        'font_size': 12,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#CFF999'
    }

    format_group = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#83CAFF'
    }

    format_group_right = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5'
    }

    format_group_left = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5'
    }

    format_group_number = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5'
    }

    format_group_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5',
        'num_format': '#,##0.00'
    }

    format_content_text = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'justify',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_center = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_left = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_number = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
    }

    format_content_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_float_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'right',
        'valign': 'vcenter',
        'bg_color': '#DDDDDD',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_date = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'yyyy-mm-dd'
    }

    format_content_time = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'hh:mm:ss'
    }

    format_content_datetime = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'yyyy-mm-dd hh:mm:ss'
    }

    format_content_bold_text = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_left = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_number = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
    }

    format_content_bold_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_title_small = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#83CAFF'
    }

    format_title_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#83CAFF',
        'num_format': '#,##0.00'
    }
