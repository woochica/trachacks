import burndown

from trac.core import *
from trac import test as tractest
from nose.tools import *

class testBasicFunctionality():

    def setUp(self):
        self.env = tractest.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        self.burndown = burndown.BurndownComponent(self.env)
        self.burndown.upgrade_environment(self.db)
        
        self.mockReq = tractest.Mock(perm=tractest.MockPerm(), href=tractest.Mock(burndown=lambda : "burndown"))

    def test_get_active_navigation_item(self):
        assert self.burndown.get_active_navigation_item(None) == 'burndown'
        
    def test_get_navigation_items(self):
        nav_items = self.burndown.get_navigation_items(self.mockReq)
        nav_items.next()

    @raises(StopIteration)
    def test_get_navigation_items_exactly_one(self):
        nav_items = self.burndown.get_navigation_items(self.mockReq)
        nav_items.next()
        nav_items.next()

    def test_get_permission_actions(self):
        permissions = self.burndown.get_permission_actions()
        assert_equals (permissions, ["BURNDOWN_VIEW", "BURNDOWN_ADMIN"])
        
    def test_match_request(self):
        req=tractest.Mock(path_info="/burndown")
        assert self.burndown.match_request(req)
        
    def test_match_request_non_matching(self):
        req=tractest.Mock(path_info="/otherUrl")
        assert not self.burndown.match_request(req)
        
    def test_start_milestone(self):
        milestone="milestone1"
        cursor = self.db.cursor()        
        cursor.execute("insert into milestone (name, due, completed, started, description) values (%s, 0, 0, 0, '');", [milestone])

        self.burndown.start_milestone(self.db, milestone)
        
        cursor.execute("SELECT started FROM milestone WHERE name = %s" , [milestone])
        row = cursor.fetchone()
        assert row
        
    @raises(TracError)
    def test_start_milestone_twice(self):
        milestone="milestone1"
        cursor = self.db.cursor()        
        cursor.execute("insert into milestone (name, due, completed, started, description) values (%s, 0, 0, 0, '');", [milestone])

        self.burndown.start_milestone(self.db, milestone)
        self.burndown.start_milestone(self.db, milestone)
        
#===============================================================================
#    def test_milestone_with_quotes(self):
#        milestone="milestone '1"
#        cursor = self.db.cursor()        
#        cursor.execute("insert into milestone (name, due, completed, started, description) values (%s, 0, 0, 0, '');", [milestone])
# 
#        self.burndown.start_milestone(self.db, milestone)
#        cursor.execute("SELECT started FROM milestone WHERE name = %s", [milestone])
#        row = cursor.fetchone()
#        assert row
#===============================================================================