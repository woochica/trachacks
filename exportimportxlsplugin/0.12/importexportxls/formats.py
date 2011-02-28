# -*- coding: utf-8 -*-

# The MIT License
# 
# Copyright (c) 2011 ben.12
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import re
import datetime
import copy
from xlwt import Alignment, easyxf
from trac.core import *
from trac.util.datefmt import get_datetime_format_hint, parse_date

_default_style = easyxf('borders: top thin, bottom thin, left thin, right thin')

class IExportFormat(Interface):
    
    def get_style():
        """Return the XStyle to use in XLS.
        """
    
    def convert(value):
        """Return the value to the well type.
        """

class NumberFormat():
    
    implements(IExportFormat)
    
    def get_style(self, value):
        style = copy.copy(_default_style)
        return style
    
    def convert(self, value):
        ret = value
        try:
            ret = float(value)
        except:
            ret = value
        return ret


class DateFormat():
    
    implements(IExportFormat)
    
    def get_style(self, value = None):
        style = copy.copy(_default_style)
        style.num_format_str = get_datetime_format_hint()
        return style
    
    def convert(self, value):
        ret = value
        if isinstance(value, int):
            ret = datetime.datetime(value)
        elif isinstance(value, unicode) or isinstance(value, str):
            ret = parse_date(value)
        if isinstance(ret, datetime.datetime):
            ret = ret.replace(tzinfo=None) # xlwt doesn't support timezone
        return ret


class TextFormat():
    
    implements(IExportFormat)
    
    def get_style(self, value = None):
        style = copy.copy(_default_style)
        if value != None and value.find('\n') != -1 :
            style.alignment = Alignment()
            style.alignment.wrap = style.alignment.WRAP_AT_RIGHT
            style.alignment.shri = style.alignment.SHRINK_TO_FIT
        return style
    
    def convert(self, value):
        value = unicode(value)
        value = value.replace('\r\n', '\n')
        value = value.replace('\r', '\n')
        value = value.strip('\n')
        return value


class BooleanFormat():
    
    implements(IExportFormat)
    
    def get_style(self, value = None):
        style = copy.copy(_default_style)
        return style
    
    def convert(self, value):
        ret = value
        try:
            ret = bool(value)
        except:
            ret = value
        return ret
