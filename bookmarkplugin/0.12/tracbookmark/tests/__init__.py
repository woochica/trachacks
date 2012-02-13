# -*- coding: utf-8 -*-

import unittest
from StringIO import StringIO

from trac.attachment import Attachment
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.ticket.model import Ticket, Milestone
from trac.versioncontrol.api import Repository
from trac.web.href import Href
from tracbookmark import BookmarkSystem


class BookmarkSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        self.req = Mock(base_path='/trac.cgi', chrome={}, args={}, session={},
                        abs_href=Href('/trac.cgi'), href=Href('/trac.cgi'),
                        locale='', perm=MockPerm(), authname='admin', tz=None)

    def tearDown(self):
        self.env.reset_db()

    def test_format_name_default_page(self):
        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/')
        self.assertEquals('wiki', data['realm'])
        self.assertEquals('/trac.cgi', data['url'])
        self.assertEquals('WikiStart', data['linkname'])

    def test_format_name_wiki(self):
        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/wiki/WikiStart')
        self.assertEquals('wiki', data['realm'])
        self.assertEquals('/trac.cgi/wiki/WikiStart', data['url'])
        self.assertEquals('WikiStart', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_wiki_default(self):
        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/wiki')
        self.assertEquals('wiki', data['realm'])
        self.assertEquals('/trac.cgi/wiki', data['url'])
        # XXX why?
        self.assertEquals('Wiki', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_wiki_versioned(self):
        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/wiki/Page/SubPage?version=42')
        self.assertEquals('wiki', data['realm'])
        self.assertEquals('/trac.cgi/wiki/Page/SubPage?version=42',
                          data['url'])
        self.assertEquals('Page/SubPage?version=42', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_ticket(self):
        ticket = Ticket(self.env)
        ticket['type'] = 'enhancement'
        ticket['summary'] = 'This is a summary'
        ticket.insert()
        tkt_id = ticket.id

        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/ticket/%d' % tkt_id)
        self.assertEquals('ticket', data['realm'])
        self.assertEquals('/trac.cgi/ticket/%d' % tkt_id, data['url'])
        self.assertEquals('#%d' % tkt_id, data['linkname'])
        self.assertEquals('enhancement: This is a summary', data['name'])

    def test_format_name_report(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO report (title,query,description) "
                       "VALUES ('Active Tickets','SELECT 1','')")
        report_id = db.get_last_id(cursor, 'report')

        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/report/%d' % report_id)
        self.assertEquals('report', data['realm'])
        self.assertEquals('/trac.cgi/report/%d' % report_id, data['url'])
        self.assertEquals('{%d}' % report_id, data['linkname'])
        self.assertEquals('Active Tickets', data['name'])

    def test_format_name_milestone(self):
        bmsys = BookmarkSystem(self.env)
        data = bmsys._format_name(self.req, '/milestone/milestone1')
        self.assertEquals('milestone', data['realm'])
        self.assertEquals('/trac.cgi/milestone/milestone1', data['url'])
        self.assertEquals('milestone:milestone1', data['linkname'])
        self.assertEquals('', data['name'])

    def test_format_name_changeset(self):
        bmsys = BookmarkSystem(self.env)

        data = bmsys._format_name(self.req, '/changeset/42/trunk')
        self.assertEquals('changeset', data['realm'])
        self.assertEquals('/trac.cgi/changeset/42/trunk', data['url'])
        self.assertEquals('[42]', data['linkname'])
        self.assertEquals('Changeset 42 in trunk', data['name'])

        data = bmsys._format_name(self.req, '/changeset/42')
        self.assertEquals('changeset', data['realm'])
        self.assertEquals('/trac.cgi/changeset/42', data['url'])
        self.assertEquals('[42]', data['linkname'])
        self.assertEquals('Changeset 42', data['name'])

        # TODO: Add unit-tests for multi-repositories


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BookmarkSystemTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
