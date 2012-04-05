#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import re
import sys
import os
import tempfile
import shutil
import unittest
import pprint
import difflib
from genshi.core import Markup

from trac.web.api import Request
from trac.env import Environment
from trac.core import TracError
#from trac.web.clearsilver import HDFWrapper

from talm_importer.importer import ImportModule

import trac
if trac.__version__.startswith('0.12'):
    CTL_EXT = '-0.12.ctl'
    TICKETS_DB = 'tickets-0.12.db'
else:
    CTL_EXT = '.ctl'
    TICKETS_DB = 'tickets.db'


def _exec(cursor, sql, args = None): cursor.execute(sql, args)

def _printme(something): pass # print something


class PrinterMarkupWrapper(object):
    def __init__(self, data):
        self.data = data

    _stringify_re = re.compile(r'\\.')

    def __repr__(self):
        def replace(match):
            val = match.group(0)
            if val == r'\n':
                return '\n'
            return val
        data = repr(self.data)[len("<Markup u'"):-len("'>")]
        return 'Markup(u"""\\\n' + self._stringify_re.sub(replace, data) + '""")'


class PrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, Markup):
            object = PrinterMarkupWrapper(object)
        elif isinstance(object, str):
            object = object.decode('utf-8')
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


class ImporterTestCase(unittest.TestCase):
    def _pformat(self, data):
        return PrettyPrinter(indent=4).pformat(data)

    def _test_preview(self, env, filename):
        req = Request({'SERVER_PORT': 0, 'SERVER_NAME': 'any', 'wsgi.url_scheme': 'any', 'wsgi.input': 'any', 'REQUEST_METHOD': 'GET' }, lambda x, y: _printme)
        try:
           from trac.test import MockPerm
           req.perm = MockPerm()
        except ImportError:
           pass
        req.authname = 'testuser'
        #req.hdf = HDFWrapper([]) # replace by this if you want to generate HTML: req.hdf = HDFWrapper(loadpaths=chrome.get_all_templates_dirs())
        template, data, content_type = ImportModule(env)._do_preview(filename, 1, req, encoding='cp1252')
        #sys.stdout = tempstdout
        #req.display(template, content_type or 'text/html')
        #open('/tmp/out.html', 'w').write(req.hdf.render(template, None))
        return self._pformat(data)

    def _test_import(self, env, filename, sheet = 1):
        req = Request({'SERVER_PORT': 0, 'SERVER_NAME': 'any', 'wsgi.url_scheme': 'any', 'wsgi.input': 'any', 'REQUEST_METHOD': 'GET' }, lambda x, y: _printme)
        try:
           from trac.test import MockPerm
           req.perm = MockPerm()
        except ImportError:
           pass
        req.authname = 'testuser'
        #req.hdf = HDFWrapper([]) # replace by this if you want to generate HTML: req.hdf = HDFWrapper(loadpaths=chrome.get_all_templates_dirs())
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "SELECT * FROM enum ORDER BY type, value, name")
        enums_before = cursor.fetchall()
        _exec(cursor, "SELECT * FROM component ORDER BY name")
        components_before = cursor.fetchall()
        #print enums_before
        # when testing, always use the same time so that the results are comparable
        #print "importing " + filename + " with tickettime " + str(ImporterTestCase.TICKET_TIME)
        template, data, content_type = ImportModule(env)._do_import(filename, sheet, req, filename,
                                                                    ImporterTestCase.TICKET_TIME, encoding='cp1252')
        #sys.stdout = tempstdout
        #req.display(template, content_type or 'text/html')
        #open('/tmp/out.html', 'w').write(req.hdf.render(template, None))
        _exec(cursor, "SELECT * FROM ticket ORDER BY id")
        tickets = cursor.fetchall()
        _exec(cursor, "SELECT * FROM ticket_custom ORDER BY ticket, name")
        tickets_custom = cursor.fetchall()
        _exec(cursor, "SELECT * FROM ticket_change")
        tickets_change = cursor.fetchall()
        _exec(cursor, "SELECT * FROM enum ORDER BY type, value, name")
        enums = [f for f in set(cursor.fetchall()) - set(enums_before)]
        _exec(cursor, "SELECT * FROM component ORDER BY name")
        components = [f for f in set(cursor.fetchall()) - set(components_before)]
        return self._pformat([ tickets, tickets_custom, tickets_change, enums, components ])

    def _readfile(self, path):
        f = open(path, 'rb')
        try:
            return f.read()
        finally:
            f.close()

    def _writefile(self, path, data):
        f = open(path, 'wb')
        try:
            return f.write(data)
        finally:
            f.close()

    def _evalfile(self, path):
        contents = self._readfile(path)
        return eval(contents), contents

    def _do_test(self, env, filename, testfun):
        from os.path import join, dirname
        testdir = join(dirname(dirname(dirname(testfolder))), 'test')
        outfilename = join(testdir, filename + '.' + testfun.__name__ + '.out')
        ctlfilename = join(testdir, filename + '.' + testfun.__name__ + CTL_EXT)
        self._writefile(outfilename, testfun(env, join(testdir, filename)))
        outdata, outprint = self._evalfile(outfilename)
        ctldata, ctlprint = self._evalfile(ctlfilename)
        try:
            self.assertEquals(ctldata, outdata)
        except AssertionError, e:
            ctlprint = self._pformat(ctldata)
            diffs = list(difflib.ndiff(ctlprint.splitlines(),
                                       outprint.splitlines()))
            def contains_diff(diffs, idx, line):
                for diff in diffs[idx - line:idx + line]:
                    if not diff.startswith(' '):
                        return True
                return False
            raise AssertionError('Two objects do not match\n' +
                                 '\n'.join(diff.rstrip()
                                           for idx, diff in enumerate(diffs)
                                           if contains_diff(diffs, idx, 2)))

    def _do_test_diffs(self, env, filename, testfun):
        self._do_test(env, filename, testfun)

    def _do_test_with_exception(self, env, filename, testfun):
        try:
           self._do_test(env, filename, testfun)
        except TracError, e:
           return str(e)

    def _setup(self, configuration = None):
        configuration = configuration or '[ticket-custom]\nmycustomfield = text\nmycustomfield.label = My Custom Field\nmycustomfield.order = 1\n'

        configuration += '\n[ticket]\ndefault_type = task\n'


        instancedir = os.path.join(tempfile.gettempdir(), 'test-importer._preview')
        if os.path.exists(instancedir):
           shutil.rmtree(instancedir, False)
        env = Environment(instancedir, create=True)
        open(os.path.join(os.path.join(instancedir, 'conf'), 'trac.ini'), 'a').write('\n' + configuration + '\n')
        db = env.get_db_cnx()
        _exec(db.cursor(), "INSERT INTO permission VALUES ('anonymous', 'REPORT_ADMIN')        ")
        _exec(db.cursor(), "INSERT INTO permission VALUES ('anonymous', 'IMPORT_EXECUTE')        ")
        db.commit()
        ImporterTestCase.TICKET_TIME = 1190909220
        return Environment(instancedir)

    def test_import_1(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1245, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'sum2', u'', u''])
        db.commit()
        self._do_test_diffs(env, 'Backlog-for-import.csv', self._test_preview)
        self._do_test_diffs(env, 'simple.csv', self._test_preview)
        self._do_test_diffs(env, 'simple.csv', self._test_preview)
        self._do_test(env, 'simple.csv', self._test_import)
        # Run again, to make sure that the lookups are done correctly
        ImporterTestCase.TICKET_TIME = 1190909221
        self._do_test(env, 'simple-copy.csv', self._test_import)
        # import after modification should throw exception
        _exec(cursor, "update ticket set changetime = " + str(ImporterTestCase.TICKET_TIME + 10) + " where id = 1245")
        db.commit()
        try:
           pass
           # TODO: this should throw an exception (a ticket has been modified between preview and import)
          #_do_test(env, 'simple-copy.csv', self._test_import)
        except TracError, err_string:
            print err_string
        #TODO: change the test case to modify the second or third row, to make sure that db.rollback() works

    def test_import_with_comments(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1245, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'sum2', u'', u''])
        db.commit()
        self._do_test_diffs(env, 'simple.csv', self._test_import)
        self._do_test_diffs(env, 'simple_with_comments.csv', self._test_preview)
        ImporterTestCase.TICKET_TIME = ImporterTestCase.TICKET_TIME + 100
        self._do_test_diffs(env, 'simple_with_comments.csv', self._test_import)

    def test_import_with_comments_and_description(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1245, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'sum2', u'', u''])
        db.commit()
        self._do_test_diffs(env, 'simple.csv', self._test_import)
        self._do_test_diffs(env, 'simple_with_comments_and_description.csv', self._test_preview)
        ImporterTestCase.TICKET_TIME = ImporterTestCase.TICKET_TIME + 100
        self._do_test_diffs(env, 'simple_with_comments_and_description.csv', self._test_import)


    def test_import_2(self):
        env = self._setup()
        self._do_test_diffs(env, 'various-charsets.xls', self._test_preview)
        self._do_test(env, 'various-charsets.xls', self._test_import)

    def test_import_3(self):
        env = self._setup()
        try:
           self._do_test_diffs(env, 'with-id.csv', self._test_preview)
           self.assert_(False)
        except TracError, e:
           self.assertEquals(str(e), 'Ticket 1 found in file, but not present in Trac: cannot import.')

    def test_import_4(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'summary before change', u'', u''])
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [2, u'defect', 1191377630, 1191377630, u'component2', None, u'major', u'somebody2', u'anonymous2', u'', u'', u'', u'new', None, u'summarybefore change', u'', u''])
        _exec(cursor, "insert into enum values (%s, %s, %s)", ['priority', 'mypriority', '1'])
        _exec(cursor, "insert into enum values (%s, %s, %s)", ['priority', 'yourpriority', '2'])
        _exec(cursor, "insert into component values (%s, %s, %s)", ['mycomp', '', ''])
        _exec(cursor, "insert into component values (%s, %s, %s)", ['yourcomp', '', ''])
        db.commit()
        self._do_test_diffs(env, 'with-id.csv', self._test_preview)
        self._do_test(env, 'with-id.csv', self._test_import)

    def test_import_5(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'a summary that is duplicated', u'', u''])
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [2, u'defect', 1191377630, 1191377630, u'component2', None, u'major', u'somebody2', u'anonymous2', u'', u'', u'', u'new', None, u'a summary that is duplicated', u'', u''])
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [3, u'defect', 1191377630, 1191377630, u'component2', None, u'major', u'somebody2', u'anonymous2', u'', u'', u'', u'new', None, u'a summary that is duplicated', u'', u''])
        db.commit()
        self.assertEquals(self._do_test_with_exception(env, 'test-detect-duplicate-summary-in-trac.csv', self._test_preview), 'Tickets #1, #2 and #3 have the same summary "a summary that is duplicated" in Trac. Ticket reconciliation by summary can not be done. Please modify the summaries to ensure that they are unique.')

    def test_import_6(self):
        env = self._setup()
        self.assertEquals(self._do_test_with_exception(env, 'test-detect-duplicate-summary-in-spreadsheet.csv', self._test_import), 'Summary "test & integration" is duplicated in the spreadsheet. Ticket reconciliation by summary can not be done. Please modify the summaries in the spreadsheet to ensure that they are unique.')

    def test_import_7(self):
        self._setup()
        instancedir = os.path.join(tempfile.gettempdir(), 'test-importer.tickets')
        if os.path.exists(instancedir):
           shutil.rmtree(instancedir, False)
        _dbfile = os.path.join(os.path.join(instancedir, 'db'), 'trac.db')
        env = Environment(instancedir, create=True)
        os.remove(_dbfile)
        shutil.copyfile(os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(testfolder))), 'test'), TICKETS_DB), _dbfile)
        open(os.path.join(os.path.join(instancedir, 'conf'), 'trac.ini'), 'a').write('\n[ticket-custom]\ndomain = text\ndomain.label = Domain\nstage = text\nstage.label = Stage\nusers = text\nusers.label = Users\n')
        env = Environment(instancedir)
        self._do_test(env, 'ticket-13.xls', self._test_import)

    def test_import_with_ticket_types(self):
        env = self._setup()
        self._do_test_diffs(env, 'simple-with-type.csv', self._test_preview)
        self._do_test_diffs(env, 'simple-with-type.csv', self._test_import)

    def test_import_with_reconciliation_by_owner(self):
        '''
        This test covers the two option flags "reconciliate_by_owner_also" and "skip_lines_with_empty_owner".
        '''
        env = self._setup('\n[ticket-custom]\neffort = text\neffort.label = My Effort\n\n[importer]\nreconciliate_by_owner_also = true\nskip_lines_with_empty_owner = true\n')
        self._do_test(env, 'same-summary-different-owners-for-reconcilation-with-owner.xls', self._test_import)

    def test_import_csv_bug(self):
        '''
        This test covers the same as precedent, plus a problem I had with CSV:
        "TracError: Unable to read this file, does not seem to be a valid Excel or CSV file:newline inside string"
        The problem disapeared when I fixed the issue in test_import_with_reconciliation_by_owner
        '''
        env = self._setup('\n[ticket-custom]\neffort = text\neffort.label = My Effort\n\n[importer]\nreconciliate_by_owner_also = true\nskip_lines_with_empty_owner = true\n')
        self._do_test(env, 'same-summary-different-owners-for-reconcilation-with-owner.csv', self._test_import)

    def test_import_not_first_worksheet(self):
        '''
        This test covers importing an index worksheet, plus a prb with an empty milestone:
  File "/Users/francois/workspace/importer/talm_importer/importer.py", line 416, in _process
    processor.process_new_lookups(newvalues)
  File "/Users/francois/workspace/importer/talm_importer/processors.py", line 128, in process_new_lookups
    lookup.insert()
  File "/sw/lib/python2.4/site-packages/Trac-0.11b1-py2.4.egg/trac/ticket/model.py", line 650, in insert
    assert self.name, 'Cannot create milestone with no name'
        '''
        env = self._setup('\n[ticket-custom]\neffort = text\neffort.label = My Effort\n\n[importer]\nreconciliate_by_owner_also = true\nskip_lines_with_empty_owner = true\n')
        def _test_import_fourth_sheet(env, filename): return self._test_import(env, filename, 4)
        self._do_test(env, 'Backlog.xls', _test_import_fourth_sheet)

    def test_import_with_id_called_id(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [1, u'defect', 1191377630, 1191377630, u'component1', None, u'major', u'somebody', u'anonymous', u'', u'', u'', u'new', None, u'summary before change', u'', u''])
        _exec(cursor, "insert into ticket values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [2, u'defect', 1191377630, 1191377630, u'component2', None, u'major', u'somebody2', u'anonymous2', u'', u'', u'', u'new', None, u'summarybefore change', u'', u''])
        _exec(cursor, "insert into enum values (%s, %s, %s)", ['priority', 'mypriority', '1'])
        _exec(cursor, "insert into enum values (%s, %s, %s)", ['priority', 'yourpriority', '2'])
        _exec(cursor, "insert into component values (%s, %s, %s)", ['mycomp', '', ''])
        _exec(cursor, "insert into component values (%s, %s, %s)", ['yourcomp', '', ''])
        db.commit()
        self._do_test_diffs(env, 'with-id-called-id.csv', self._test_preview)
        self._do_test(env, 'with-id-called-id.csv', self._test_import)

    def test_import_non_ascii_ticket_4458(self):
        env = self._setup()
        self._do_test_diffs(env, 'non_ascii_ticket_4458.csv', self._test_preview)

    def test_ticket_6220(self):
        env = self._setup()
        db = env.get_db_cnx()
        cursor = db.cursor()
        _exec(cursor, "insert into session values (%s,1,1174683538)", ["newuser2"])
        db.commit()
        self._do_test_diffs(env, 'multiple_new_users_ticket_6220.csv', self._test_preview)

    def test_status_ticket_7679(self):
        env = self._setup()
        self._do_test_diffs(env, 'importing_status_ticket_7679.csv', self._test_import)

    def test_project_ticket_7679(self):
        env = self._setup('\n[ticket-custom]\nproject = text\nproject.label = My Project\n\n')
        self._do_test_diffs(env, 'importing_project_ticket_7679.csv', self._test_import)

    def test_status_ticket_7658(self):
        env = self._setup()
        self._do_test_diffs(env, 'importing_status_ticket_7658.csv', self._test_preview) 
        self._do_test_diffs(env, 'importing_status_ticket_7658.csv', self._test_import)

    def test_preview_ticket_7205(self):
        env = self._setup()
        self._do_test_diffs(env, 'simple_for_7205.csv', self._test_import)
        # preview after import... should now show any "modified-"
        self._do_test_diffs(env, 'simple_for_7205.csv', self._test_preview) 

    def test_dates_ticket_8357(self):
        env = self._setup('\n[ticket-custom]\nmydate = text\nproject.label = My Date\nmydatetime = text\nproject.label = My DateTime\n\n')
        self._do_test_diffs(env, 'datetimes.xls', self._test_preview) 
        self._do_test_diffs(env, 'datetimes.xls', self._test_import)

    def test_dates_formatted_ticket_8357(self):
        env = self._setup('\n[ticket-custom]\nmydate = text\nproject.label = My Date\nmydatetime = text\nproject.label = My DateTime\n[importer]\ndatetime_format=%x %X\n')
        self._do_test_diffs(env, 'datetimes_formatted.xls', self._test_preview) 
        self._do_test_diffs(env, 'datetimes_formatted.xls', self._test_import)

    def test_celltypes_ticket_8804(self):
        env = self._setup("""\
[importer]
datetime_format=%Y-%m-%d %H:%M
""")
        self._do_test_diffs(env, 'celltypes-ticket-8804.xls', self._test_preview)
        self._do_test_diffs(env, 'celltypes-ticket-8804.xls', self._test_import)

    def test_restkey_ticket_9730(self):
        env = self._setup()
        self._do_test_diffs(env, 'restkey_9730.csv', self._test_import)
        self._do_test_diffs(env, 'restkey_9730.csv', self._test_preview) 

    def test_newticket_empty_status(self):
        env = self._setup()
        self._do_test_diffs(env, 'newticket_empty_status.csv', self._test_preview) 
        self._do_test_diffs(env, 'newticket_empty_status.csv', self._test_import)

    def test_empty_columns(self):
        env = self._setup()
        self._do_test_diffs(env, 'empty_columns.csv', self._test_preview) 
        self._do_test_diffs(env, 'empty_columns.csv', self._test_import)


def suite():
    return unittest.makeSuite(ImporterTestCase, 'test')
    #return unittest.TestSuite( [ ImporterTestCase('test_import_with_ticket_types') ])
if __name__ == '__main__':
    testfolder = __file__
    unittest.main(defaultTest='suite')
