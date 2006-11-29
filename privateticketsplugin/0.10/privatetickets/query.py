from trac.core import *
from trac.web.api import IRequestFilter
from trac.ticket.query import QueryModule, Query
from trac.mimeview.api import Mimeview, IContentConverter
from trac.wiki import wiki_to_html
from trac.util.datefmt import http_date
from trac.util.text import CRLF

from StringIO import StringIO

from api import PrivateTicketsSystem

__all__ = ['PrivateTicketsQueryFilter']

class PrivateTicketsQueryFilter(Component):
    """Remove entires from queries if this user shouldn't see them."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if isinstance(handler, QueryModule) and req.args.get('format'):
            self.log.debug('PrivateTickets: Intercepting formatted query')
            return self # XXX: Hack due to IContentConverter being b0rked <NPK>
        return handler
      
    def post_process_request(self, req, template, content_type):
        if req.args.get('DO_PRIVATETICKETS_FILTER') == 'query':
            # Extract the data
            results = []
            node = req.hdf.getObj('query.results')
            if not node:
                return template, content_type
            node = node.child()
            
            while node:
                data = {}
                sub_node = node.child()
                while sub_node:
                    data[sub_node.name()] = sub_node.value()
                    sub_node = sub_node.next()
                results.append(data)
                node = node.next()
                
            self.log.debug('PrivateTickets: results = %r', results)
            # Nuke the old data
            req.hdf.removeTree('query.results')
            
            # Filter down the data
            fn = PrivateTicketsSystem(self.env).check_ticket_access
            new_results = [d for d in results if fn(req, d['id'])]
            
            self.log.debug('PrivateTickets: new_results = %r', new_results)

            # Reinsert the data
            req.hdf['query.results'] = new_results
                
        return template, content_type

    # Content conversion insanity
    def process_request(self, req):
        constraints = QueryModule(self.env)._get_constraints(req)
        if not constraints and not req.args.has_key('order'):
            # avoid displaying all tickets when the query module is invoked
            # with no parameters. Instead show only open tickets, possibly
            # associated with the user
            constraints = {'status': ('new', 'assigned', 'reopened')}
            if req.authname and req.authname != 'anonymous':
                constraints['owner'] = (req.authname,)
            else:
                email = req.session.get('email')
                name = req.session.get('name')
                if email or name:
                    constraints['cc'] = ('~%s' % email or name,)

        query = Query(self.env, constraints, req.args.get('order'),
                      req.args.has_key('desc'), req.args.get('group'),
                      req.args.has_key('groupdesc'),
                      req.args.has_key('verbose'))
                      
        format = req.args.get('format')
        self.send_converted(req, 'trac.ticket.Query', query, format, 'query')
    
    def get_supported_conversions(self):
        yield ('csv', 'Comma-delimited Text', 'csv',
               'trac.ticket.Query', 'text/csv', 9)
               
    def convert_content(self, req, mimetype, query, key):
        if key == 'rss':
            return self.export_rss(req, query) + ('rss',)
        elif key == 'csv':
            return self.export_csv(req, query, mimetype='text/csv') + ('csv',)
        elif key == 'tab':
            return self.export_csv(req, query, '\t', 'text/tab-separated-values') + ('tsv',)

    def send_converted(self, req, in_type, content, selector, filename='file'): # Stolen from Mimetype
        """Helper method for converting `content` and sending it directly.

        `selector` can be either a key or a MIME Type."""
        from trac.web import RequestDone
        content, output_type, ext = self.convert_content(req, in_type,
                                                         content, selector)
        req.send_response(200)
        req.send_header('Content-Type', output_type)
        req.send_header('Content-Disposition', 'filename=%s.%s' % (filename,
                                                                   ext))
        req.end_headers()
        req.write(content)
        raise RequestDone 

    # Hacked content converters
    def export_csv(self, req, query, sep=',', mimetype='text/plain'):
        self.log.debug('PrivateTicket: Running hacked CSV converter')
        content = StringIO()
        cols = query.get_columns()
        content.write(sep.join([col for col in cols]) + CRLF)

        fn = PrivateTicketsSystem(self.env).check_ticket_access
        results = query.execute(req, self.env.get_db_cnx())
        for result in results:
            # Filter data
            if not fn(req, result['id']):
                continue
        
            content.write(sep.join([unicode(result[col]).replace(sep, '_')
                                                        .replace('\n', ' ')
                                                        .replace('\r', ' ')
                                    for col in cols]) + CRLF)
        return (content.getvalue(), '%s;charset=utf-8' % mimetype)

    def export_rss(self, req, query):
        query.verbose = True
        db = self.env.get_db_cnx()
        fn = PrivateTicketsSystem(self.env).check_ticket_access
        results = [r for r in query.execute(req, db) if fn(req, r['id'])]
        for result in results:
            result['href'] = req.abs_href.ticket(result['id'])
            if result['reporter'].find('@') == -1:
                result['reporter'] = ''
            if result['description']:
                # unicode() cancels out the Markup() returned by wiki_to_html
                descr = wiki_to_html(result['description'], self.env, req, db,
                                     absurls=True)
                result['description'] = unicode(descr)
            if result['time']:
                result['time'] = http_date(result['time'])
        req.hdf['query.results'] = results
        req.hdf['query.href'] = req.abs_href.query(group=query.group,
                groupdesc=query.groupdesc and 1 or None,
                verbose=query.verbose and 1 or None,
                **query.constraints)
        return (req.hdf.render('query_rss.cs'), 'application/rss+xml')
