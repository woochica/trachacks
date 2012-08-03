#
# Narcissus plugin for Trac
#
# Copyright (C) 2008 Kim Upton    
# All rights reserved.    
#

class NarcissusSettings(object):

    DEFAULT_BOUNDS = {'wiki': [20, 50, 100],
                      'svn': [50, 150, 300],
                      'ticket': [3, 9, 18]
                     }
    DEFAULT_CREDITS = {'open': 1,
                       'accept': 3,
                       'comment': 1,
                       'update': 1,
                       'close': 3
                      }
    
    def __init__(self, db):
        cursor = db.cursor()

        cursor.execute('select value from narcissus_settings where type = "resource"')
        self.resources = []
        for row in cursor:
            self.resources.append(row[0])

        cursor.execute('select value from narcissus_settings where type = "member"')
        self.members = []
        for row in cursor:
            self.members.append(row[0])
        
        self.bounds = {}
        for r in self.resources:
            cursor.execute('''select threshold from narcissus_bounds where 
                resource = "%s" order by level''' % r)
            self.bounds[r] = [row[0] for row in cursor]
        if not self.bounds:
            self.bounds = self.DEFAULT_BOUNDS
        
        cursor.execute('select type, credit from narcissus_credits')
        self.credits = {}
        for row in cursor:
            self.credits[row[0]] = row[1]
        if not self.credits:
            self.credits = self.DEFAULT_CREDITS
