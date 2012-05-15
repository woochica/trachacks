from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor

from model import CodeReview


class CodeReviewerSystem(Component):
    """System management for codereviewer plugin."""
    
    implements(IEnvironmentSetupParticipant, IPermissionRequestor)
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.current_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        self.current_db_version = self._get_version(db.cursor())
        if self.current_db_version < CodeReview.db_version:
            return True
        if self.current_db_version > CodeReview.db_version:
            raise TracError(_('Database newer than CodeReviewer version'))
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        for i in range(self.current_db_version + 1, CodeReview.db_version + 1):
            name  = 'db%i' % i
            try:
                upgrades = __import__('upgrades', globals(), locals(), [name])
                script = getattr(upgrades, name)
            except AttributeError:
                raise TracError(_('No CodeReviewer upgrade module %(num)i '
                                  '(%(version)s.py)', num=i, version=name))
            script.do_upgrade(self.env, cursor)
            self._set_version(cursor, i)
            db.commit()
            
    def _get_version(self, cursor):
        cursor.execute("SELECT value FROM system " +\
                       "WHERE name=%s", (CodeReview.db_name,))
        value = cursor.fetchone()
        return int(value[0]) if value else 0
            
    def _set_version(self, cursor, ver):
        cursor.execute("UPDATE system SET value=%s WHERE name=%s",
                       (ver,CodeReview.db_name))
        if cursor.rowcount==0:
            cursor.execute("INSERT INTO system (value,name) VALUES (%s,%s)",
                           (ver,CodeReview.db_name))
            
        self.log.info('Upgraded CodeReviewer version from %d to %d',ver-1,ver)
    
    
    # IPermissionRequestor methods  
    def get_permission_actions(self):
        return ['CODEREVIEWER_MODIFY']
