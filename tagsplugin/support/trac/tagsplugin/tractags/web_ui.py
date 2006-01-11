from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from StringIO import StringIO

class TagsLi(Component):
    implements(IRequestHandler,ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/tagli'
                
    def process_request(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cs = db.cursor()
        tag = req.args.get('tag')
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        buf = StringIO()
        if tag:
            buf.write('WHERE tag LIKE \'%s%s\'' % (tag,'%'))
            
        cursor.execute('SELECT DISTINCT tag FROM tags %s ORDER BY tag' % (buf.getvalue()))

        msg = StringIO()

        msg.write('<ul>')
        while 1:
            row = cursor.fetchone()
            if row == None:
                 break

            t = row[0]
            msg.write('<li>')
            msg.write(t)
            msg.write('</li>')

        msg.write('</ul>')
        req.write(msg.getvalue())

    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tagsupport', resource_filename(__name__, 'htdocs'))]
    
