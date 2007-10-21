import xmlrpclib
import posixpath

from trac.core import *
from tracrpc.api import IXMLRPCHandler, expose_rpc

class NikoNikoRPC(Component):
    """ Interface to NikoNiko Calendar """

    implements(IXMLRPCHandler)

    def xmlrpc_namespace(self):
        return 'nikoniko'

    def xmlrpc_methods(self):
        yield ('NIKONIKO_VIEW', ((str, ),), self.getCurrentMood)
        yield ('NIKONIKO_VIEW', ((str, ),), self.getCurrentComment)
    
    def page_info(self, name, time, author, version, comment=''):
        return dict(name=name,
                    lastModified=xmlrpclib.DateTime(int(time)),
                    author=author,
                    version=int(version),
                    comment=(comment or '') )

    def getCurrentMood(self, req):
        todays_mood = getField(req, 'nikoniko_mood')
        if todays_mood:
            return 'okMood'
        else:
            return todays_mood

    def getCurrentComment(self, req):
        comment = getField(req, 'nikoniko_comment')
        if comment:
            return 'Ok'
        else:
            return comment
    
    def getField(self, req, field):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        now = datetime.datetime.now()
        date_time = now.strftime("%d/%m/%Y");
        username = req.authname;
        getMoodSQL = "SELECT " + field + " FROM nikoniko WHERE "\
                     "nikoniko_username = '" + username + "' AND "\
                     "nikoniko_date = '" + date_time + "'"
        cursor.execute(getMoodSQL)
        row = cursor.fetchone()
        if row: 
            return row[0] 
        else:
            return null 