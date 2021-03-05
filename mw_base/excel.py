# -*- coding: utf-8 -*-

__title__ = 'excel'
__version__ = '0.0.1'
__build__ = 0x000001
__author__ = 'Zolzaya E.'
__copyright__ = 'Copyright 2011 Zolzaya E.'


from xlwt import Workbook, Worksheet, easyxf, Formula

from abc import ABCMeta, abstractmethod

from io import StringIO
import base64
import types
import string

# Cell styles
STYLE_TEXT = easyxf('font: name Times New Roman, bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_TEXT_WITHOUT_BORDERS = easyxf('font: name Times New Roman, bold off; align: wrap on, vert bottom, horiz left;')
STYLE_TEXT_CENTER_BOLD = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;pattern: pattern solid, fore_color light_turquoise')
STYLE_TEXT_CENTER = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_TEXT_CENTER_PERCENT = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='0.00%')
STYLE_TEXT_CENTER_PERCENT1 = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00')
STYLE_TEXT_LEFT = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_TEXT_LEFT_NO_WRAP = easyxf('font: name Times New Roman; align: wrap off, vert centre, horiz left;')
STYLE_TEXT_LEFT_BOLD = easyxf('font: name Times New Roman, bold on;align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_TEXT_LEFT_BOLD_NO_WRAP = easyxf('font: name Times New Roman, bold on, height 160;align: wrap off, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_TEXT_RIGHT = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00')
STYLE_TEXT_RIGHT_NO_PREC = easyxf('font: name Times New Roman, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0')
STYLE_TEXT_RIGHT_NO_WRAP = easyxf('font: name Times New Roman; align: wrap off, vert centre, horiz right;')
STYLE_TEXT_RIGHT_BOLD = easyxf('font: name Times New Roman, bold on;align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
STYLE_HEADING = easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz center;')
STYLE_HEADING_NO_WRAP = easyxf('font: name Times New Roman, bold on; align: wrap off, vert centre, horiz center;')
STYLE_HEADING_LARGE = easyxf('font: name Times New Roman, bold on, height 200; align: wrap on, vert centre, horiz center;')
STYLE_HEADING_TEXT_LEFT = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue')
STYLE_HEADING_TEXT_CENTER = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_CENTER_WITHOUT_COLOR = easyxf('font: name Times New Roman, bold on, height 180; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_RIGHT = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_RIGHT_NO_PREC = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0')
STYLE_HEADING2_TEXT_LEFT = easyxf('font: name Times New Roman, bold on, height 150; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise')
STYLE_HEADING2_TEXT_CENTER = easyxf('font: name Times New Roman, bold on, height 150; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise')
STYLE_HEADING2_TEXT_RIGHT = easyxf('font: name Times New Roman, bold on, height 150; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise', num_format_str='#,##0.00')
STYLE_HEADING2_TEXT_RIGHT_NO_PREC = easyxf('font: name Times New Roman, bold on, height 150; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise', num_format_str='#,##0')
STYLE_HEADING2_TEXT_LEFT_NO_WRAP = easyxf('font: name Times New Roman, bold on, height 150; align: wrap off, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise')
STYLE_HEADING2_TEXT_RIGHT_NO_WRAP = easyxf('font: name Times New Roman, bold on, height 150; align: wrap off, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color light_turquoise', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_RIGHT_RIGHT = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_CENTER_CENTER = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;')
#easyxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
STYLE_TEXT_CENTER_WITHOUT_BORDERS = easyxf('font: name Times New Roman, bold off; align: wrap on, vert bottom, horiz center;')
STYLE_TEXT_RIGHT_WITHOUT_BORDERS = easyxf('font: name Times New Roman, bold off; align: wrap on, vert bottom, horiz right;')
STYLE_TEXT_RIGHT_BOLD_WITHOUT_BORDERS = easyxf('font: name Times New Roman, bold on; align: wrap on, vert bottom, horiz right;')
STYLE_TEXT_LEFT_BOLD_WITHOUT_BORDERS = easyxf('font: name Times New Roman, bold on; align: wrap on, vert bottom, horiz left;')
STYLE_HEADING_TEXT_ORIENTATION_90_CC = easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz center, rota +90; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color pale_blue')
STYLE_CELL_FORE_COLOUR = easyxf('pattern: pattern solid, fore_colour black;')
STYLE_FORMATED_NUMBER = easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00')
STYLE_HEADING_TEXT_CENTER_YELLOW = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color yellow')
STYLE_HEADING_TEXT_CENTER_GREEN = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color lime')
STYLE_HEADING_TEXT_CENTER_PALE_BLUE = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue')
STYLE_HEADING_TEXT_CENTER_BLUE = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color blue')
STYLE_HEADING_TEXT_CENTER_DARK_BLUE = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color dark_blue')
STYLE_HEADING_TEXT_CENTER_RED = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color red')
STYLE_HEADING_TEXT_CENTER_ORANGE = easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color orange')

# Orientation constants
PORTRAIT = True
LANDSCAPE = False

def get_excel_headers_by_letter():
    headers = [letter for letter in string.ascii_uppercase]
    for l1 in string.ascii_uppercase:
        for l2 in string.ascii_uppercase:
            headers.append(l1+l2)
    return headers

def ignore_error(formula, default=0):
    return "IF(ISERROR({0}), {1}, ({0}))".format(formula, default)

def formula_round(formula, digits=1):
    return "ROUND({0}, {1})".format(formula, digits)

class InvalidData(Exception):
    "Data is invalid or empty"


class InvalidObjectType(Exception):
    "Object type is invalid."


class InvalidCellStyle(Exception):
    "Style is invalid."


class IndexOutOfRange(Exception):
    "Index out of range"


class Cell(object):
    """

    """
    # Data
    _data = None

    # row
    _row = None

    # column
    _column = None

    # style
    _style = None

    # width
    _width = None

    # height
    _height = None

    # formula
    _formula = None

    def __init__(self, row, column, data=None, style=None, width=3, height=0.5):
        self.row = row
        self.column = column
        self.data = data
        self.style = style
        self.height = height
        self.width = width

    def __str__(self):
        return "ROW: %s, COLUMN: %s, DATA: %s, STYLE: %s" % (self.row, self.column, self.data, self.style)

    ####################################################
    # -------------- GETTERS AND SETTERS --------------#
    ####################################################
    @property
    def data(self):
        if self._formula:
            return Formula(self._formula)
        return self._data

    @data.setter
    def data(self, data):
#        data = str(data)
#        self._data = data.decode("utf-8")
        self._data = data

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, row):
        if isinstance(row, types.IntType):
            self._row = [row]
        elif isinstance(row, types.ListType):
            self._row = row
        else:
            raise InvalidObjectType()

    @property
    def column(self):
        return self._column

    @column.setter
    def column(self, column):
        if isinstance(column, types.IntType):
            self._column = [column]
        elif isinstance(column, types.ListType):
            self._column = column
        else:
            raise InvalidObjectType()

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, formula):
        self._formula = formula

    @property
    def style(self):
        if not self._style:
            return STYLE_TEXT
        return self._style

    @style.setter
    def style(self, style):
        self._style = style

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = int(width*700)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        self._height = int(height*700)


class Element(object):

    # cells
    _cells = None

    def __init__(self):
        self._cells = list()

    def add_sheet_cell_at(self, row, column, sheet, cell, style=None, width=3, height=0.5):
        sheet_cell = "'{0}'!{1}".format(sheet, cell)
        self.add_formula(row, column, sheet_cell, style, width, height)

    def add_formula(self, row, column, formula, style=None, width=3, height=0.5):
        cell = Cell(row, column, 0, style, width, height)
        cell.formula = formula
        self.append(cell)

    def add_cell(self, row, column, data, style=None, width=3, height=0.5):
        self.append(Cell(row, column, data, style, width, height))

    def append(self, cell):
        self._cells.append(cell)

    def size(self):
        return len(self._cells)

    def delete_cell_at(self, index):
        del self._cells[index]

    def get_cell_at(self, row, column):
        for cell in self.cells:
            if cell.row[0] == row and cell.column[0] == column:
                return self.cells.index(cell)

    def set_cell_style_at(self, row, column, style):
        self.cells[self.get_cell_at(row, column)].style = style

    def set_cell_data_at(self, row, column, data):
        self.cells[self.get_cell_at(row, column)].data = data

    def set_cell_at(self, index, cell):
        if not isinstance(cell, Cell):
            raise InvalidObjectType()
        if index > self.size():
            raise IndexOutOfRange()
        self._cells[index] = cell

    def add_raw_cells(self, datas):
        for data in datas:
            self.append(Cell(data[0], data[1], data[2]))

    @property
    def cells(self):
        return self._cells

    @cells.setter
    def cells(self, cells):
        if not isinstance(cells, types.ListType):
            raise InvalidObjectType()
        self._cells = cells


class Sheet(object):

    # name
    _name = None

    # elements of sheet
    _elements = None

    # reference of sheet
    _ref = None

    # orientation
    _orientation = None

    def __init__(self, name):
        self._name = None
        self.name = name
        self._elements = list()
        self._ref = None
        self._orientation = PORTRAIT


    def build(self, workbook):
        self._ref = None
        self._ref = workbook.add_sheet(self.name, cell_overwrite_ok=True)
        self._ref.set_portrait(self._orientation)
        for element in self.elements:
            self._write_element(element)
    
    def img2bmp(path):
        import Image
        import StringIO
        img = Image.open(path)
        f = StringIO.StringIO()
        img.save(f, "bmp")
        return f
    
    def _write_cell(self, cell):
        if not isinstance(cell, Cell):
            raise InvalidObjectType()
        # write a merged cell
        if len(cell.row) == 2 and len(cell.column) == 2:
            self._ref.write_merge(
                                  cell.row[0]
                                  , cell.row[1]
                                  , cell.column[0]
                                  , cell.column[1]
                                  , cell.data
                                  , cell.style)
        # write cell
        elif type(cell.data) == type([]):
            self._ref.insert_bitmap(
                                    cell.data[0],
                                    cell.row[0],
                                    cell.column[0])
        else:
            self._ref.write(
                            cell.row[0]
                            , cell.column[0]
                            , cell.data
                            , cell.style)
        self._ref.row(cell.row[0]).height = cell.height
        self._ref.col(cell.column[0]).width = cell.width
        self._ref.set_header_margin(0.3)
        self._ref.set_footer_margin(0.2)
        self._ref.set_top_margin(0.1)
        self._ref.set_bottom_margin(0)
        self._ref.set_left_margin(0)
        self._ref.set_right_margin(0)

    def _write_element(self, element):
        for cell in element.cells:
            self._write_cell(cell)

    ####################################################
    # -------------- GETTERS AND SETTERS --------------#
    ####################################################
    def orientation(self, orientation):
        self._orientation = orientation

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, types.StringType):
            raise InvalidObjectType()
        self._name = name

    @property
    def elements(self):
        return self._elements

    def add_elements(self, elements):
        if isinstance(elements, Element):
            self._elements.append(elements)
        elif isinstance(elements, types.ListType):
            self._elements += elements
        else:
            raise InvalidObjectType()

    @elements.setter
    def elements(self, elements):
        self._elements = list()
        self.add_elements(elements)


class Excel(object):

    # Excel workbook
    _workbook = None

    # Sheets
    _sheets = None

    def __init__(self):
        self._sheets = list()

    def __init_vars(self):
        self._workbook = None
        self._sheets = []
        self._workbook = Workbook(encoding='utf8')

    def build_from_raw(self, data):
        self.__init_vars()

    def build(self, sheets=list()):
        self.__init_vars()
        self.add_sheets(sheets)
        for sheet in self.sheets:
            if not isinstance(sheet, Sheet):
                raise InvalidObjectType()
            sheet.build(self._workbook)
        return self._output()

    def _output(self):
        buffer = StringIO()
        self.workbook.save(buffer)
        buffer.seek(0)
        out = base64.encodestring(buffer.getvalue())
        buffer.close()
        # clear
        del self._workbook
        del self._sheets
        del buffer
        # return result
        return out

    ####################################################
    # -------------- GETTERS AND SETTERS --------------#
    ####################################################
    @property
    def workbook(self):
        return self._workbook

    @workbook.setter
    def workbook(self, workbook):
        self._workbook = workbook

    @property
    def sheets(self):
        return self._sheets

    def add_sheets(self, sheets):
        if isinstance(sheets, Sheet):
            self._sheets.append(sheets)
        elif isinstance(sheets, types.ListType):
            if not self._sheets:
                self._sheets = sheets
            else:
                self._sheets += sheets
        else:
            raise InvalidObjectType()

    @sheets.setter
    def sheets(self, sheets):
        self._sheets = list()
        self.add_sheets(sheets)

class Report(object):

    __metaclass__ = ABCMeta

    # sheets
    sheets = []

    # cursor
    cr = None

    # start row
    _sr = 0

    # start column
    _sc = 0

    def _inc_sr(self, num=1):
      self._sr += num
      return self._sr

    def _inc_sc(self, num=1):
      self._sc += num
      return self._sc

    def fill_cells(self, element, x1, y1, x2, y2, data='', style=None, width=3, height=0.5):
        x = x1
        while(x <= x2):
            y = y1
            while(y <= y2):
                cell = Cell(x, y, data, style, width, height)
                element.append(cell)
                y += 1
            x += 1

    def get_sheets(self):
        return self.sheets

    def execute(self, query):
        return self.cr.execute(query)

    def fetch_one(self, query):
        self.execute(query)
        return self.cr.dictfetchone()

    def fetch_all(self, query):
        self.execute(query)
        return self.cr.dictfetchall()
