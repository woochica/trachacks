import re
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href

class TicketWebUiAddon(Component):
    implements(INavigationContributor)
    
    def __init__(self):
        pass
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ""

    def get_navigation_items(self, req):

        # skip anonymous requests:
        if (req.authname == 'anonymous'):
            return []

        # skip non-ticket requests:
        mo = re.match('/(ticket)/(\d+)', req.path_info)
        if (not mo):
            return []

        username = req.authname
        type = mo.group(1);
        id = mo.group(2);
        
        unread_link = self.get_unread_link(username, type, id)

        return [ ('metanav', "last-unread", unread_link) ]

    def get_unread_link(self, username, type, id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        title = "Last unread"
        link = "#content"

        cursor.execute( """
          SELECT last_read_on
          FROM trac_unread
          WHERE username = %s
            AND type = %s
            AND id = %s
          """, (username, type, id) )
        try:
            last_read_on = int(cursor.fetchone()[0])
            cursor.execute( """
              SELECT oldvalue
              FROM ticket_change
              WHERE field = 'comment'
                AND ticket = %s
                AND time > %s
              ORDER BY time
              """, (id, last_read_on) )
            try:
                unread_comment = cursor.fetchone()[0]
                
                # replies have 'originalcomment.reply' format
                # like 12.13 (if comment:13 was a reply to comment:12)
                mo = re.search('\.(\d+)$', unread_comment)
                if (mo):
                    unread_comment = mo.group(1);

                unread_comment = int(unread_comment)
                link = "#comment:%d" % unread_comment
            except:
                title = "No unread"
                link = "#edit"
        except:
            pass

        cursor.close()
        db.commit();

        unread_link = Markup('<a href="%s">%s</a>' % (link, title) )
        
        return unread_link
