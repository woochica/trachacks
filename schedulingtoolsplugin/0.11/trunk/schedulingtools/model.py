# from pysqlite2 import dbapi2 as sqlite
from trac.core import *

try:
    import pysqlite2.dbapi2 as sqlite
    have_pysqlite = 2
except ImportError:
    try:
        import sqlite3 as sqlite
        have_pysqlite = 2
    except ImportError:
        try:
            import sqlite
            have_pysqlite = 1
        except ImportError:
            have_pysqlite = 0

class Availability(object):
    "blabla"
    
    def find(cls, db, name):
        cursor = db.cursor()
        cursor.execute("SELECT name,validFrom,validUntil,weekdays,resources,workFrom,workUntil FROM AVAILABILITY WHERE name='%s'" % (name))
        av = None
        for row in cursor:
            av = Availability()
            av.name = row[0]
            av.validFrom = row[1]
            av.validUntil = row[2]
            av.weekdays = row[3]
            av.resources = row[4]
            av.workFrom = row[5]
            av.workUntil = row[6]
        cursor.close()    
        return av;
    find = classmethod(find)
    
    def save(self, db, name):
        ""
        cursor = db.cursor()
        cursor.execute("UPDATE AVAILABILITY SET name=%s,validFrom=%s,validUntil=%s,weekdays=%s,resources=%s,workFrom=%s,workUntil=%s WHERE name=%s",
                       (self.name, self.validFrom,self.validUntil,self.weekdays,self.resources,self.workFrom,self.workUntil,name))
        if cursor.rowcount==0:
            cursor.execute("INSERT INTO AVAILABILITY (name,validFrom,validUntil,weekdays,resources,workFrom,workUntil) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                           (self.name, self.validFrom,self.validUntil,self.weekdays,self.resources,self.workFrom,self.workUntil))
        cursor.close()
        db.commit()
        
    def delete(self, db):
        ""
        cursor = db.cursor()
        cursor.execute("DELETE FROM AVAILABILITY WHERE name=%s", [self.name])
        cursor.close()
        db.commit()
    
class Availabilities(object):
    
    def get(cls, db):

        cursor = db.cursor()
        try:
            cursor.execute("SELECT name,validFrom,validUntil,weekdays,resources,workFrom,workUntil FROM AVAILABILITY")
        except sqlite.OperationalError:
            cursor.execute("CREATE TABLE AVAILABILITY(name varchar(255),validFrom varchar(20),validUntil varchar(20),weekdays varchar(255),resources varchar(255),workFrom char(5),workUntil char(5))")
            cursor.execute("SELECT name,validFrom,validUntil,weekdays,resources,workFrom,workUntil FROM AVAILABILITY")
        result = []
        for row in cursor:
            av = Availability()
            av.name = row[0]
            av.validFrom = row[1]
            av.validUntil = row[2]
            av.weekdays = row[3]
            av.resources = row[4]
            av.workFrom = row[5]
            av.workUntil = row[6]
            result.append(av)
            
        cursor.close()    
        return result
    get = classmethod(get)

    def reset(cls, db):
        cursor = db.cursor()
        cursor.execute("DROP TABLE AVAILABILITY")
        db.commit()
    reset = classmethod(reset)
    
