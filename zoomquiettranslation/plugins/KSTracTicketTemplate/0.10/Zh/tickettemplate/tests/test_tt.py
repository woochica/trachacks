from trac.core import *
from trac.test import EnvironmentStub, Mock
from trac.env import Environment
from trac.core import ComponentManager, ComponentMeta

import tickettemplate.ttadmin as ttadmin

import os.path
import tempfile
import shutil

import unittest

class TicketTemplateTestCase(unittest.TestCase):

    def setUp(self):
#        self.env = EnvironmentStub()

        env_path = os.path.join(tempfile.gettempdir(), 'trac-tempenv')
        self.env = Environment(env_path, create=True)
        self.db = self.env.get_db_cnx()
        
        self.compmgr = ComponentManager()

        # init TicketTemplateModule
        self.tt = ttadmin.TicketTemplateModule(self.compmgr)
        setattr(self.tt, "env", self.env)

    def tearDown(self):
        self.db.close()
        self.env.shutdown() # really closes the db connections
        shutil.rmtree(self.env.path)

    def test_get_active_navigation_item(self):
        req = Mock(path_info='/tickettemplate')
        self.assertEqual('tickettemplate', self.tt.get_active_navigation_item(req))

        req = Mock(path_info='/something')
        self.assertNotEqual('tickettemplate', self.tt.match_request(req))

    def test_get_navigation_items(self):
        req = Mock(href=Mock(tickettemplate=lambda:"/trac-tempenv/tickettemplate"))
        a, b, c= self.tt.get_navigation_items(req).next()
        self.assertEqual('mainnav', a)
        self.assertEqual('tickettemplate', b)

    def test_match_request(self):
        req = Mock(path_info='/tickettemplate')
        self.assertEqual(True, self.tt.match_request(req))

        req = Mock(path_info='/something')
        self.assertEqual(False, self.tt.match_request(req))

    def test_getTicketTypeNames(self):
        options = self.tt._getTicketTypeNames()
        self.assertEqual(["default", "defect", "enhancement", "task"], options)

    def test_loadSaveTemplateText(self):
        for tt_name, tt_text in [("default", "default text"), 
                                ("defect", "defect text"), 
                                ("enhancement", "enhancement text"), 
                                ("task", "task text"),
                                ]:
            self.tt._saveTemplateText(tt_name, tt_text)
            self.assertEqual(tt_name + " text", self.tt._loadTemplateText(tt_name))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketTemplateTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main()
