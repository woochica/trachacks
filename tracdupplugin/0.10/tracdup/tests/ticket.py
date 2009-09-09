from trac.test import EnvironmentStub
from trac.core import TracError
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule

from tracdup import ticket

import time

import unittest

class TracDupTestCase(unittest.TestCase):

    def setUp(self):
        # we need default_data so that things like status get set correctly
        self.env = EnvironmentStub(default_data=True)
        #import code; code.interact(local=locals())

        # add our custom fields
        self.env.config.set('ticket-custom', 'dup_of',    'text')
        self.env.config.set('ticket-custom', 'dups',      'text')
        self.env.config.set('ticket-custom', 'dup_count', 'text')

        from trac import log
        # FIXME: this doesn't work
        self.env.log = log.logger_factory(logtype='stderr', level='DEBUG')
        import sys
        # NO REALLY I WANT TO SEE MY OUTPUT
        self.env.log.warning = lambda _: sys.stdout.write('%s\n' % _)
        self.env.log.debug = lambda _: sys.stdout.write('%s\n' % _)
        self.env.log.warning('Hey I am here')
        
        self.ticket_module = TicketModule(self.env)
        self.comp = ticket.TracDupPlugin(self.env)

    def _create_a_ticket(self):
        ticket = Ticket(self.env)
        ticket['reporter'] = 'santa'
        ticket['summary'] = 'Foo'
        ticket['description'] = 'Bar'
        ticket['foo'] = 'This is a custom field'
        ticket['status'] = 'new'
        ticket.insert()
        return ticket

    def test_dup_ok(self):
        t1 = self._create_a_ticket()
        t2 = self._create_a_ticket()
        t2['dup_of'] = '1'
        t2.save_changes('test', 'test')

        t1 = Ticket(self.env, 1)
        self.assertEquals(t1['dups'], '2')
        self.assertEquals(t1['dup_count'], '1')

        t2 = Ticket(self.env, 2)
        self.assertEquals(t2['dup_of'], '1')

    def test_dup_undup(self):
        self.test_dup_ok()

        time.sleep(1)
        t2 = Ticket(self.env, 2)
        # break the chain
        t2['dup_of'] = None
        t2.save_changes('test', 'test')

        t1 = Ticket(self.env, 1)
        self.assertEquals(t1['dups'], None)
        self.assertEquals(t1['dup_count'], None)

        t2 = Ticket(self.env, 2)
        self.assertEquals(t2['dup_of'], None)

    def test_dup_recursively(self):
        t1 = self._create_a_ticket()
        t2 = self._create_a_ticket()
        t3 = self._create_a_ticket()
        t4 = self._create_a_ticket()

        # first dup 2 to 1
        self.env.log.debug('TEST: dup 2 to 1')
        t2['dup_of'] = '1'
        t2.save_changes('test', 'test')

        t1 = Ticket(self.env, 1)
        self.assertEquals(t1['dups'], '2')
        self.assertEquals(t1['dup_count'], '1')

        t2 = Ticket(self.env, 2)
        self.assertEquals(t2['dup_of'], '1')

        # don't break integrity
        time.sleep(1)

        # now dup 3 to 2
        self.env.log.debug('TEST: dup 3 to 2')
        t3['dup_of'] = '2'
        t3.save_changes('test', 'test')

        t2 = Ticket(self.env, 2)
        self.assertEquals(t2['dups'], '3')
        self.assertEquals(t2['dup_count'], '1')

        t3 = Ticket(self.env, 3)
        self.assertEquals(t3['dup_of'], '2')

        # and 4 to 2
        self.env.log.debug('TEST: dup 4 to 2')
        t4['dup_of'] = '2'
        t4.save_changes('test', 'test')

        t2 = Ticket(self.env, 2)
        self.assertEquals(t2['dups'], '3, 4')
        self.assertEquals(t2['dup_count'], '2')

        t4 = Ticket(self.env, 3)
        self.assertEquals(t4['dup_of'], '2')

        # now notice how crowded ticket 1 is
        self.env.log.debug('TEST: validate 1')
        t1 = Ticket(self.env, 1)
        self.assertEquals(t1['dups'], '2, 3, 4')
        self.assertEquals(t1['dup_count'], '3')

    def test_closed_does_not_dup_to_None(self):
        # tests that dup_of can go from non-existing to None
        # (when a pre-existing ticket gets changed, and custom fields added)
        t1 = self._create_a_ticket()

        self.failIf(t1.values.has_key('dup_of'))

        # apparently setting status to new didn't get saved; assert it
        t1 = Ticket(self.env, 1)
    
        self.assertEquals(t1['status'], 'new')
        self.failIf(t1.values.has_key('dup_of'))

        # close the ticket
        t1['status'] = 'closed'
        t1['resolution'] = 'fixed'
        t1.save_changes('test', 'test', when=1)
        
        t1 = Ticket(self.env, 1)
        self.assertEquals(t1['status'], 'closed')
        self.failIf(t1.values.has_key('dup_of'))

        # t1 does not have dup_of set at all, set it to ''
        # as if the summary was changed through the web ui and try to save
        t1['dup_of'] = ''
        t1['summary'] = 'changed summary'
        t1.save_changes('test', 'test', when=2)

        t1 = Ticket(self.env, 1)
        self.failUnless(t1.values.has_key('dup_of'))

        # make sure the status did not get changed at all
        self.assertEquals(t1['status'], 'closed')
        self.assertEquals(t1['resolution'], 'fixed')

    # validation gets triggered through web_ui, so we test
    # the validate method directly
    def test_validate_ok(self):
        t1 = self._create_a_ticket()
        t2 = self._create_a_ticket()
        t2['dup_of'] = '1'

        r = self.comp.validate_ticket(None, t2)
        self.failIf(r, "Should not have gotten error %r" % (r, ))

    def test_validate_no_ticket(self):
        t = self._create_a_ticket()
        t['dup_of'] = ''

        r = self.comp.validate_ticket(None, t)
        self.failIf(r)

    def test_validate_change_with_dups(self):
        # first create 1 and 2, and dup 2 to 1
        t1 = self._create_a_ticket()
        t2 = self._create_a_ticket()
        t2['dup_of'] = '1'

        r = self.comp.validate_ticket(None, t2)
        self.failIf(r)
        t2.save_changes('test', 'test')

        # now, make a change to t1 without changing dup_count or dups
        t1 = Ticket(self.env, 1)
        t1['status'] = 'closed'
        t1['resolution'] = 'fixed'

        r = self.comp.validate_ticket(None, t1)
        self.failIf(r, "validation failed with %r" % r)

    def test_no_validate_self(self):
        t = self._create_a_ticket()
        t['dup_of'] = '1'

        r = self.comp.validate_ticket(None, t)
        self.failUnless(r)

    def test_no_validate_self_str(self):
        t = self._create_a_ticket()
        # set id as a str, like when it comes from a request
        t.id = '1'
        t['dup_of'] = '1'

        r = self.comp.validate_ticket(None, t)
        self.failUnless(r)

    def test_no_validate_closed_dup_to_self(self):
        # had a bug in production where I set dup_of on a closed ticket,
        # and dupped to self, and caused recursion depth exceeded
        t = self._create_a_ticket()
        t['status'] = 'closed'
        t['resolution'] = 'duplicate'
        t.save_changes('test', 'test')

        t['dup_of'] = '1'

        r = self.comp.validate_ticket(None, t)
        self.failUnless(r,
            "Should not have validated closed ticket dupped to self")

    def test_no_validate_reopen_with_dup_of(self):
        # had a bug in production where I set dup_of on a closed ticket,
        # and reopened at the same time
        t = self._create_a_ticket()
        t = self._create_a_ticket()
        t['status'] = 'closed'
        t['resolution'] = 'duplicate'
        t.save_changes('test', 'test')

        t['dup_of'] = '1'

        t['status'] = 'reopened'
        t['resolution'] = None

        r = self.comp.validate_ticket(None, t)
        self.failUnless(r,
            "Should not validated ticket reopened and dup_of'd at same time")
        self.assertEquals(r[0][0], 'status')
        self.failUnless('already closed' in r[0][1])

    def test_validate_reopened_dup(self):
        # had a bug in production where I set dup_of on a closed ticket,
        # and reopened at the same time
        # but a previously reopened ticket should of course be dup_of'able
        t = self._create_a_ticket()
        t = self._create_a_ticket()
        t['status'] = 'closed'
        t['resolution'] = 'duplicate'
        t.save_changes('test', 'test', when=1)

        t['status'] = 'reopened'
        t['resolution'] = None
        t.save_changes('test', 'test', when=2)

        t['dup_of'] = '1'
        r = self.comp.validate_ticket(None, t)
        self.failIf(r)

    def test_no_validate_inexistant(self):
        t = self._create_a_ticket()
        t['dup_of'] = '2'

        self.assertRaises(TracError, self.comp.validate_ticket, None, t)

    def test_no_validate_wrong_ticket(self):
        t = self._create_a_ticket()
        t['dup_of'] = '#1'

        r = self.comp.validate_ticket(None, t)
        self.failUnless(r)

if __name__ == '__main__':
    unittest.main()
