# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Jun Omae <jun66j5@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import shutil
import tempfile
import unittest
from StringIO import StringIO
from pkg_resources import parse_version

from trac import __version__ as TRAC_VERSION
from trac.attachment import Attachment
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.ticket.model import Ticket
from trac.web.href import Href
from trac.wiki.model import WikiPage

from tracbookmark import BookmarkSystem


class BookmarkSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        self.env.path = tempfile.mkdtemp()
        self.req = Mock(base_path='/trac.cgi', chrome={}, args={}, session={},
                        abs_href=Href('/trac.cgi'), href=Href('/trac.cgi'),
                        locale='', perm=MockPerm(), authname='admin', tz=None)
        self.bmsys = BookmarkSystem(self.env)

    def tearDown(self):
        self.env.reset_db()
        shutil.rmtree(self.env.path)

    def test_format_name_default_page(self):
        data = self.bmsys._format_name(self.req, '/')
        self.assertEquals('wiki', data['class_'])
        self.assertEquals('/trac.cgi', data['href'])
        self.assertEquals('WikiStart', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_wiki(self):
        data = self.bmsys._format_name(self.req, '/wiki/WikiStart')
        self.assertEquals('wiki', data['class_'])
        self.assertEquals('/trac.cgi/wiki/WikiStart', data['href'])
        self.assertEquals('WikiStart', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_wiki_default(self):
        data = self.bmsys._format_name(self.req, '/wiki')
        self.assertEquals('wiki', data['class_'])
        self.assertEquals('/trac.cgi/wiki', data['href'])
        self.assertEquals('WikiStart', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_wiki_versioned(self):
        data = self.bmsys._format_name(self.req, '/wiki/Page/SubPage?version=42')
        self.assertEquals('wiki', data['class_'])
        self.assertEquals('/trac.cgi/wiki/Page/SubPage?version=42',
                          data['href'])
        self.assertEquals('Page/SubPage@42', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_new_ticket(self):
        ticket = Ticket(self.env)
        ticket['type'] = 'enhancement'
        ticket['summary'] = 'This is a summary'
        ticket['status'] = 'new'
        ticket.insert()
        tkt_id = ticket.id

        data = self.bmsys._format_name(self.req, '/ticket/%d' % tkt_id)
        self.assertEquals('new ticket', data['class_'])
        self.assertEquals('/trac.cgi/ticket/%d' % tkt_id, data['href'])
        self.assertEquals('#%d' % tkt_id, data['linkname'])
        self.assertEquals('enhancement: This is a summary (new)', data['name'])

    def test_format_name_closed_ticket(self):
        ticket = Ticket(self.env)
        ticket['type'] = 'defect'
        ticket['summary'] = 'This is a summary'
        ticket['status'] = 'closed'
        ticket.insert()
        tkt_id = ticket.id

        data = self.bmsys._format_name(self.req, '/ticket/%d' % tkt_id)
        self.assertEquals('closed ticket', data['class_'])
        self.assertEquals('/trac.cgi/ticket/%d' % tkt_id, data['href'])
        self.assertEquals('#%d' % tkt_id, data['linkname'])
        self.assertEquals('defect: This is a summary (closed)', data['name'])

    def test_format_name_missing_ticket(self):
        tkt_id = 1

        data = self.bmsys._format_name(self.req, '/ticket/%d' % tkt_id)
        self.assertEquals('missing ticket', data['class_'])
        self.assertEquals(None, data['href'])
        self.assertEquals('#%d' % tkt_id, data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_report(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO report (title,query,description) "
                       "VALUES ('Active Tickets','SELECT 1','')")
        report_id = db.get_last_id(cursor, 'report')

        data = self.bmsys._format_name(self.req, '/report/%d' % report_id)
        self.assertEquals('report', data['class_'])
        self.assertEquals('/trac.cgi/report/%d' % report_id, data['href'])
        self.assertEquals('{%d}' % report_id, data['linkname'])
        self.assertEquals('Active Tickets', data['name'])

    def test_format_name_milestone(self):
        data = self.bmsys._format_name(self.req, '/milestone/milestone1')
        self.assertEquals('milestone', data['class_'])
        self.assertEquals('/trac.cgi/milestone/milestone1', data['href'])
        self.assertEquals('milestone:milestone1', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_changeset(self):
        data = self.bmsys._format_name(self.req, '/changeset/42/trunk')
        self.assertEquals('changeset', data['class_'])
        self.assertEquals('/trac.cgi/changeset/42/trunk', data['href'])
        self.assertEquals('[42]', data['linkname'])
        if parse_version(TRAC_VERSION) < parse_version('0.12'):
            self.assertEquals('Changeset 42', data['name'])
        else:
            self.assertEquals('Changeset 42 in trunk', data['name'])

        data = self.bmsys._format_name(self.req, '/changeset/42')
        self.assertEquals('changeset', data['class_'])
        self.assertEquals('/trac.cgi/changeset/42', data['href'])
        self.assertEquals('[42]', data['linkname'])
        self.assertEquals('Changeset 42', data['name'])

    def test_format_name_attachment(self):
        attachment = Attachment(self.env, 'wiki', 'WikiStart')
        attachment.insert('foo.txt', StringIO(''), 1)
        data = self.bmsys._format_name(self.req,
                                       '/attachment/wiki/WikiStart/foo.txt')
        self.assertEquals('attachment', data['class_'])
        self.assertEquals('/trac.cgi/attachment/wiki/WikiStart/foo.txt',
                          data['href'])
        self.assertEquals("Attachment 'foo.txt' in WikiStart",
                          data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_missing_attachment(self):
        data = self.bmsys._format_name(self.req,
                                       '/attachment/wiki/WikiStart/foo.txt')
        self.assertEquals('missing attachment', data['class_'])
        self.assertEquals(None, data['href'])
        self.assertEquals("Attachment 'foo.txt' in WikiStart",
                          data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_attachment_list(self):
        data = self.bmsys._format_name(self.req,
                                       '/attachment/wiki/WikiStart')
        self.assertEquals('attachment', data['class_'])
        self.assertEquals('/trac.cgi/attachment/wiki/WikiStart/',
                          data['href'])
        self.assertEquals("Attachments of WikiStart",
                          data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_attachment_list(self):
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BookmarkSystemTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
