# from pysqlite2 import dbapi2 as sqlite
from trac.core import *
import db_default

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

class Review(object):
    "blabla"
    
    def get(cls, db, rev, author):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT author,reviewer,comment,status FROM CODEREVIEW WHERE rev='%s'" % (rev))
        except sqlite.OperationalError:
            cursor.execute("CREATE TABLE CODEREVIEW(rev varchar(10),author varchar(255),reviewer varchar(255),comment varchar(20000),status varchar(15))")
            cursor.execute("SELECT author,reviewer,comment,status FROM CODEREVIEW WHERE rev='%s'" % (rev))
        review = Review()
        review.rev = rev
        review.reviewer = ""
        review.author = author
        review.comment = ""
        review.status = "REJECTED"
        for row in cursor:
            review.author = row[0]
            review.reviewer = row[1]
            review.comment = row[2]
            review.status = row[3]
        cursor.close()    
        return review;
    get = classmethod(get)
    
    def save(self, db):
        ""
        cursor = db.cursor()
        cursor.execute("UPDATE CODEREVIEW SET author=%s,reviewer=%s,comment=%s,status=%s WHERE rev=%s",
                       (self.author,self.reviewer, self.comment,self.status,self.rev))
        if cursor.rowcount==0:
            cursor.execute("INSERT INTO CODEREVIEW (rev, author, reviewer, comment, status) VALUES (%s,%s,%s,%s,%s)",
                           (self.rev, self.author, self.reviewer, self.comment,self.status))
        cursor.close()
        db.commit()
