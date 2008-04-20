import re
from trac.core import *
from trac.web import IRequestFilter;
from time import time

class TracUnreadFilter(Component):
    implements(IRequestFilter)
    
    def __init__(self):
        pass
   
    def save_view_into_db(self, username, last_read_on, type, id):
        last_read_on = `last_read_on`;
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            sql = """
            UPDATE trac_unread
            SET last_read_on = %s
            WHERE username = %s
              AND type = %s
              AND id = %s
            """
            cursor.execute(sql, (last_read_on, username, type, id))
            if ( cursor.rowcount == 0 ):
                self.env.log.debug ("UPDATE updated no rows, trying INSERT")
                sql = """
                INSERT INTO trac_unread
                (last_read_on, username, type, id)
                VALUES
                (%s, %s, %s, %s)
                """
                cursor.execute(sql, (last_read_on, username, type, id))
        except Exception, e:
            self.env.log.debug ("Query failed: %s\nSQL:\n%s\n", e, sql)
        
        cursor.close()
        db.commit();
        
        return
    
    # IRequestFilter method
    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

    def _post_process_request(self, req):
        # skip anonymous requests:
        if (req.authname == 'anonymous'):
            return

        # skip non-ticket requests:
        mo = re.match('/(ticket)/(\d+)', req.path_info)
        if (not mo):
            return
        
        username = req.authname
        last_read_on = int(time())
        type = mo.group(1)
        id = mo.group(2)

        self.env.log.debug ("QQ: saving %s #%s view (%d)", type, id, last_read_on)

        # now, save this view into DB
        self.save_view_into_db(username, last_read_on, type, id)

    # for ClearSilver templates (trac 0.10 and below)
    def post_process_request(self, req, template, content_type):
        self._post_process_request(req)
        return (template, content_type)
    
    # for Genshi templates (trac 0.11)
    # def post_process_request(self, req, template, data, content_type):
    #     self._post_process_request(req)
    #     return (template, data, content_type)
