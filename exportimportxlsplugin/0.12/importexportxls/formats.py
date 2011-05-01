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
import copy
from xlwt import *
from xlrd import *
from trac.core import *
from trac.util.datefmt import *

_default_style = easyxf('borders: top thin, bottom thin, left thin, right thin')

class IExportFormat(Interface):
    
    def __init__(config):
        """Construdtor"""
    
    def get_style():
        """Return the XStyle to use in XLS.
        """
    
    def convert(value):
        """Return the value to the well XLS type.
        """
    
    def restore(value):
        """Return the value to the well TRAC type.
        """

class NumberFormat():
    
    implements(IExportFormat)
    
    def __init__(self, config):
        self.config = config
        self.style = copy.copy(_default_style)
    
    def get_style(self, value):
        return self.style
    
    def convert(self, value):
        ret = value
        try:
            ret = float(value)
        except:
            ret = value
        return ret
    
    def restore(self, value):
        ret = unicode(value)
        if ret.find('.') != -1:
            ret = ret.rstrip('0')
            ret = ret.rstrip('.')
        return ret

class DateFormat():
    
    implements(IExportFormat)
    
    def __init__(self, config):
        self.config = config
        self.style = copy.copy(_default_style)
        self.style.num_format_str = 'yyyy-mm-dd'
        
        date_format = self.config.get('datefield', 'format', 'dmy')
        date_sep = self.config.get('datefield', 'separator', '/')
        self.datefieldformat = { 
            'dmy': '%%d%s%%m%s%%Y',
            'mdy': '%%m%s%%d%s%%Y',
            'ymd': '%%Y%s%%m%s%%d' 
        }.get(date_format, '%%d%s%%m%s%%Y')%(date_sep, date_sep)
    
    def get_style(self, value = None):
        return self.style
    
    def convert(self, value):
        ret = value
        try:
            if isinstance(value, int):
                ret = to_datetime(value)
            elif isinstance(value, unicode) or isinstance(value, str):
                try:
                    ret = parse_date(unicode(value), hint='date')
                except:
                    try: 
                        import datefield
                        ret = datetime.strptime(value, self.datefieldformat);
                    except ImportError:
                        ret = value
        except:
            ret = value
        if isinstance(ret, datetime):
            ret = ret.replace(tzinfo=None) # xlwt doesn't support timezone
        return ret
    
    def restore(self, value):
        ret = value
        try:
            try:
                ret = xldate_as_tuple(ret, 0)
                ret = datetime(ret[0], ret[1], ret[2], ret[3], ret[4], ret[5])
            except:
                ret = value
            if isinstance(value, int):
                ret = to_datetime(value)
            elif isinstance(value, unicode) or isinstance(value, str):
                try:
                    ret = parse_date(unicode(value), hint='date')
                except:
                    try: 
                        import datefield
                        ret = datetime.strptime(value, self.datefieldformat);
                    except ImportError:
                        ret = value
        except:
            ret = ret
        
        try: 
            import datefield
            if isinstance(ret, datetime):
                ret = ret.strftime(self.datefieldformat);
        except ImportError:
            ret = format_date(ret)
        return ret


class DateTimeFormat():
    
    implements(IExportFormat)
    
    def __init__(self, config):
        self.config = config
        self.style = copy.copy(_default_style)
        self.style.num_format_str = 'yyyy-mm-dd hh:mm:ss'
    
    def get_style(self, value = None):
        return self.style
    
    def convert(self, value):
        ret = value
        try:
            if isinstance(value, int):
                ret = to_datetime(value)
            elif isinstance(value, unicode) or isinstance(value, str):
                ret = parse_date(unicode(value), hint='datetime')
        except:
            ret = value
        if isinstance(ret, datetime):
            ret = ret.replace(tzinfo=None) # xlwt doesn't support timezone
        return ret
    
    def restore(self, value):
        ret = value
        try:
            try:
                ret = xldate_as_tuple(ret, 0)
                ret = datetime(ret[0], ret[1], ret[2], ret[3], ret[4], ret[5])
            except:
                ret = value
            if isinstance(value, int):
                ret = to_datetime(value)
            elif isinstance(value, unicode) or isinstance(value, str):
                ret = parse_date(unicode(value), hint='datetime')
        except:
            ret = value
        return format_datetime(ret)


class TextFormat():
    
    implements(IExportFormat)
    
    def __init__(self, config):
        self.config = config
        self.style1 = copy.copy(_default_style)
        self.style2 = copy.copy(_default_style)
        self.style2.alignment = Alignment()
        self.style2.alignment.wrap = self.style2.alignment.WRAP_AT_RIGHT
        self.style2.alignment.shri = self.style2.alignment.SHRINK_TO_FIT
    
    def get_style(self, value = None):
        style = self.style1
        if value != None and value.find('\n') != -1 :
            style = self.style2
        return style
    
    def convert(self, value):
        value = unicode(value)
        value = value.replace('\r\n', '\n')
        value = value.replace('\r', '\n')
        value = value.strip('\n')
        return value
    
    def restore(self, value):
        value = self.convert(value)
        return value


class BooleanFormat():
    
    implements(IExportFormat)
    
    def __init__(self, config):
        self.config = config
        self.style = copy.copy(_default_style)
    
    def get_style(self, value = None):
        return self.style
    
    def convert(self, value):
        ret = value
        try:
            ret = int(value)
        except:
            ret = value
        try:
            ret = bool(ret)
        except:
            ret = ret
        return ret
    
    def restore(self, value):
        ret = value
        try:
            ret = int(value)
        except:
            ret = value
        if isinstance(ret, int) and value > 0:
            ret = '1'
        else:
            ret = '0'
        return ret
