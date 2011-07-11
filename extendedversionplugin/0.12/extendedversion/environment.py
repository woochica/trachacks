import pkg_resources

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider

db_version = 1
upgrades = [
    [], # zero-indexing
    [ # First revision
        #-- Add the milestone_version table for mapping milestones to versions
        """CREATE TABLE milestone_version (
            milestone    text PRIMARY KEY,
            version      text
        );""",
        """INSERT INTO system (name, value) VALUES ('extended_version_plugin', 1)""",
    ],
]


class EnvironmentSetup(Component):
    implements(IEnvironmentSetupParticipant, ITemplateProvider)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        # Don't need to do anything when the environment is created
        pass

    def environment_needs_upgrade(self, db):
        dbver = self._get_version(db)

        if dbver == db_version:
            return False
        elif dbver > db_version:
            raise TracError(_('Database newer than ExtendedVersionTracPlugin version'))
        self.log.info("ExtendedVersionTracPlugin schema version is %d, should be %d",
                      dbver, db_version)
        return True

    def upgrade_environment(self, db):
        dbver = self._get_version(db)

        cursor = db.cursor()
        for i in range(dbver + 1, db_version + 1):
            for sql in upgrades[i]:
                cursor.execute(sql)
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='extended_version_plugin'", (db_version,))
        self.log.info('Upgraded ExtendedVersionTracPlugin schema from %d to %d',
                      dbver, db_version)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
       return [('extendedversion', pkg_resources.resource_filename('extendedversion', 'htdocs'))]

    def get_templates_dirs(self):
       return [pkg_resources.resource_filename('extendedversion', 'templates')]


    # internal methods

    def _get_version(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='extended_version_plugin'")
        row = cursor.fetchone()
        if row:
            return int(row[0])
        else:
            return 0
