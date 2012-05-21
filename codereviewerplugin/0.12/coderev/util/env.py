# fake trac env - minimal needed for CodeReviewer

class Env(object):
    def __init__(self, db_cnx):
        self.db_cnx = db_cnx
    def get_db_cnx(self):
        return self.db_cnx
