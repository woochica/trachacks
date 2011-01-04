#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import csv
import datetime

from trac.core import TracError


def get_reader(filename, sheet_index, datetime_format):
    # NOTE THAT the sheet index is 1-based !
    # KISS - keep it simple: if it can be opened as XLS, do, otherwise try as CSV.
    try:
        return XLSReader(filename, sheet_index, datetime_format)
    except ImportError:
        try:
            return CSVReader(filename)
        except:
            raise TracError('XLS reading is not configured, and this file is not a valid CSV file: unable to read file.')
    except IndexError:
            raise TracError('The sheet index (' + str(sheet_index) + ') does not seem to correspond to an existing sheet in the spreadsheet')
    except Exception, e:
        try:
            return CSVReader(filename)
        except:
            raise TracError('Unable to read this file, does not seem to be a valid Excel or CSV file.')


class CP1252DictReader(csv.DictReader):
    def next(self):
        d = csv.DictReader.next(self)
        return dict([(key, value.decode('cp1252', 'replace')) for key, value in d.iteritems()])

class CSVReader(object):
    def __init__(self, filename):
        self.file =  open(filename, "rb")
        reader = csv.reader(self.file)
        self.csvfields = reader.next()
            
    def get_sheet_count():
        return 1
        
    def readers(self):
        return self.csvfields, CP1252DictReader(self.file, self.csvfields)
            
    def close(self):
        self.file.close()

class XLSReader(object):
    def __init__(self, filename, sheet_index, datetime_format):
        import xlrd
        self.book = xlrd.open_workbook(filename)
        self.sheetcount = self.book.nsheets
        self.sh = self.book.sheet_by_index(sheet_index - 1)
        self._datetime_format = datetime_format

    def get_sheet_count():
        return self.sheetcount
        
    def readers(self):
        import xlrd
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
