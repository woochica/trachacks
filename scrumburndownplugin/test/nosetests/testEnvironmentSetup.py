import burndown

from trac import test

class testEnvironmentSetup():

    def setUp(self):
        self.env = test.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        self.burndown = burndown.BurndownComponent(self.env)
        
    def test_upgrade_environment(self):
        self.burndown.upgrade_environment(self.db)
        assert self.burndown.environment_needs_upgrade(self.db) == False
        
    def test_environment_needs_upgrade(self):
        assert self.burndown.environment_needs_upgrade(self.db) == True
        
