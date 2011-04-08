#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import codecs
import csv
import datetime
try:
    import xlrd
except ImportError:
    xlrd = None

from trac.core import TracError


def get_reader(filename, sheet_index, datetime_format, encoding='utf-8'):
    # NOTE THAT the sheet index is 1-based !
    # KISS - keep it simple: if it can be opened as XLS, do, otherwise try as CSV.
    if xlrd:
        try:
            return XLSReader(filename, sheet_index, datetime_format)
        except IndexError:
            raise TracError('The sheet index (%s) does not seem to correspond to an existing sheet in the spreadsheet'
                            % sheet_index)
        except Exception:
            pass

    try:
        return CSVReader(filename, encoding)
    except UnicodeDecodeError:
        raise TracError('Unable to read the CSV file with "%s"' % encoding)
    except:
        if xlrd:
            message = 'Unable to read this file, does not seem to be a valid Excel or CSV file.'
        else:
            message = 'XLS reading is not configured, and this file is not a valid CSV file: unable to read file.'
        raise TracError(message)

class UTF8Reader(object):
    def __init__(self, file, encoding):
        self.reader = codecs.getreader(encoding)(file, 'replace')

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class CSVDictReader(csv.DictReader):
    def __init__(self, reader, fieldnames):
        csv.DictReader.__init__(self, reader, fieldnames)

    def next(self):
        d = csv.DictReader.next(self)
        def to_unicode(arg):
            return arg and arg.decode('utf-8')
        return dict((to_unicode(key), to_unicode(value)) for key, value in d.iteritems())

class CSVReader(object):
    def __init__(self, filename, encoding):
        self.file = open(filename, 'rb')
        self.file_reader = UTF8Reader(self.file, encoding)
        self.csv_reader = csv.reader(self.file_reader)
        self.csvfields = self.csv_reader.next()
        if self.csvfields and self.csvfields[0].startswith('\xEF\xBB\xBF'):
            # Skip BOM
            self.csvfields[0] = self.csvfields[0][3:]
        
    def get_sheet_count(self):
        return 1
        
    def readers(self):
        return self.csvfields, CSVDictReader(self.file_reader, self.csvfields)
            
    def close(self):
        self.file.close()

class XLSReader(object):
    def __init__(self, filename, sheet_index, datetime_format):
        self.book = xlrd.open_workbook(filename)
        self.sheetcount = self.book.nsheets
        self.sh = self.book.sheet_by_index(sheet_index - 1)
        self._datetime_format = datetime_format

    def get_sheet_count(self):
        return self.sheetcount
        
    def readers(self):
        # TODO: do something with sh.name. Probably add it as a column. 
        # TODO: read the other sheets. What if they don't have the same columns ?
        header = []
        for cx in range(self.sh.ncols):
            header.append(self.sh.cell_value(rowx=0, colx=cx))

        data = []
        for rx in range(self.sh.nrows):
            if rx == 0:
                continue
            row = {}
            i = 0
            for cx in range(self.sh.ncols):
                row[header[i]] = self.sh.cell_value(rx, cx)
                if self.sh.cell_type(rx, cx) == xlrd.XL_CELL_DATE:
                    row[header[i]] = datetime.datetime(*xlrd.xldate_as_tuple(row[header[i]], self.book.datemode)).strftime(self._datetime_format)

                i += 1
            data.append(row)

        return header, data

    def close(self):
        pass
