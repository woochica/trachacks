from trac.core import *
import re, random

class randomwiki():

    def __init__(self,db):
        self.db = db
        return
    
    def getentries(self,sourcepage,number): 
        '''\
        Return number random bullet items from sourcepage, stored in db.
        '''

        cursor = self.db.cursor()
        cursor.execute('''SELECT text
                          FROM wiki
                          WHERE name = %(name)s 
                          ORDER BY version desc
                          LIMIT 1''',
                           {'name':sourcepage,})
        row = cursor.fetchone()

        if row is None:
            return ''

        items = []
        r = re.compile(r'^\s*\*\s*.+$',re.MULTILINE)
        for m in r.finditer(row[0]):
            items.append(m.group(0))

        if number > len(items):
            return items
        else:
            return random.sample(items,number)

