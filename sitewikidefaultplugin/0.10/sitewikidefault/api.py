from trac.core import *
from trac.config import Option
from trac.env import IEnvironmentSetupParticipant
from trac.wiki.model import WikiPage

import os

class SiteWikiDefaultModule(Component):
    """Import some modified default wiki text on env creation."""

    defaults_path = Option('site', 'wiki_default', default='/etc/trac/wiki-default',
                           doc='Folder to search for page files')

    implements(IEnvironmentSetupParticipant)
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO system (name, value) VALUES (%s, %s)', ('sitewikidefault', '0'))
        db.commit()
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',('sitewikidefault',))
        row = cursor.fetchone()
        if not row or row[0] == '1': return False
    
        try:
            files = os.listdir(self.defaults_path)
        except os.error, e:
            raise TracError('Invalid site wiki_default path: %s'%e)
            
        db = self.env.get_db_cnx()
            
        for file in files:
            data = open(os.path.join(self.defaults_path, file), 'r').read()
            page = WikiPage(self.env, name=file, db=db)
            if data.strip() == '__delete__':
                if page.exists:
                    page.delete(db=db)
            else:
                page.text = data
                page.save('trac', 'Initializing site defaults', '127.0.0.1', db=db)
                
        cursor = db.cursor()
        cursor.execute('UPDATE system SET value=%s WHERE name=%s',('1', 'sitewikidefault'))

        db.commit()


    def upgrade_environment(self, db):
        pass
