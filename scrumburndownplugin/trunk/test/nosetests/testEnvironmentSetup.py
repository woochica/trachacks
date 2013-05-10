import burndown

from trac import test


class testEnvironmentSetup():
    def setUp(self):
        self.env = test.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        self.burndown = burndown.BurndownComponent(self.env)

    def test_environment_created(self):
        assert self.burndown.environment_needs_upgrade(self.db) is True
        self.burndown.environment_created()
        assert self.burndown.environment_needs_upgrade(self.db) is False

    def test_upgrade_environment(self):
        self.burndown.upgrade_environment(self.db)
        assert self.burndown.environment_needs_upgrade(self.db) is False

    def test_upgrade_environment_twice(self):
        assert self.burndown.environment_needs_upgrade(self.db) is True
        self.burndown.upgrade_environment(self.db)
        assert self.burndown.environment_needs_upgrade(self.db) is False
        self.burndown.upgrade_environment(self.db)

    def test_environment_needs_upgrade(self):
        assert self.burndown.environment_needs_upgrade(self.db) is True
