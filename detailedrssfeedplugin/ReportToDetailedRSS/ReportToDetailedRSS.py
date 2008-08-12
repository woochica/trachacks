from trac.web.api import IRequestFilter
from trac.core import implements, Component
from trac.db import get_column_names
from trac.resource import Resource
from trac.util.datefmt import format_datetime
from trac.web.chrome import add_link, ITemplateProvider
from trac.util.translation import _
from trac.ticket.report import ReportModule
import re

class ReportToDetailedRSS(Component):
    implements(IRequestFilter, ITemplateProvider)
    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""
    
    
    #ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return []
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    
    #IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        rmodule = ReportModule(self.env)
        #report's match request. if it's gonna be true then we'll stick in our translator,
        #but only if there's a report id (i.e. it's actually a report page)
        if rmodule.match_request(req) and 'id' in req.args and req.args.get('action', 'view') == 'view':
            add_link(req, 'alternate', '?format=rss&detailed=true' , _('Detailed RSS Feed'),
                'application/rss+xml', 'rss')
        return handler
        
    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Always returns a tuple of (template, content_type), even if
        unchanged."""
        return (template, content_type)
        
    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        """
        
        if template == "report.rss" and req.args.get('detailed','false') == 'true':
            self.env.log.debug("Detailed Feed Requested.")
            return self.intercept_report_rss(req,data)
        return (template, data, content_type)
    
    
    def intercept_report_rss(self,req,data):
        #figure out which headers are being used
        # - iterate through data's header_groups' list of lists of dictionaries
        # - I'm assuming that each group has identical headers (should always be the case), so I can check only the first header group
        titles = []
        for header in data['header_groups'][0]:
            titles.append(header['col'].strip('_'))
        #Note that "titles" is not used at this point. Because of aliasing in sql, it would be hard to figure out which title means which column
        
        
        #figure out which tickets are listed
        # - iterate through data's row_groups list of lists of dictionaries
        # - I need to check each row group, but the rss feed won't be grouped (it's only time-sorted) so I can then ignore the groupings
        ticket_ids = set()
        ticket_ids.update([row['resource'].id for (_, row_group) in data['row_groups'] for row in row_group])
        self.env.log.debug("Tickets in Report: %s" % ticket_ids)
        
        #generate data based on the headers and the ticket ids
        # - actually, for now I'm just going by the ticket ids because the headers will be tricky: SQL aliasing will make it so I can't just use them verbatim
        #  - oddly enough, the query module will make this work, because it can't alias.
        # - make sure tickets that have been *created* but not *modified* show up in the list
        #  - this is easy with a LEFT JOIN
        #  - COALESCE is used to pick values from the ticket if they don't exist in the change
        # - we're now using our own template, so we don't have to obey report.rss's rules anymore.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        idstring = ','.join([str(s) for s in ticket_ids])
        
        #if their limit is set to '0', sqlite will return 0 rows. thus, make it -1 instead
        limit = self.config.getint('report','items_per_page_rss',-1) or -1
        
        #all the fields starting with 'tc_' will get printed for *all* changes.
        #fields without this prefix will only get printed once for each set of changes.
        sql = """SELECT
            t.summary AS summary,
            t.id AS id,
            t.owner AS owner,
            t.priority AS priority,
            t.milestone AS milestone,
            t.component AS component,
            t.version AS version,
            t.cc AS cc,
            t.keywords AS keywords,
            COALESCE(tc.time, t.time) AS changetime,
            COALESCE(tc.author, t.reporter) AS reporter,
            tc.field AS tc_field,
            tc.oldvalue AS tc_oldvalue,
            tc.newvalue AS tc_newvalue
            FROM ticket t
            LEFT JOIN ticket_change tc ON t.id = tc.ticket
            WHERE t.id IN (%(ids)s)
            ORDER BY changetime ASC
            LIMIT %(limit)s;
            """ % {'ids':idstring,'limit':limit}
        
        cursor.execute(sql)
        
        #convert the rows to dictionaries keyed off of the column names, so we need to find the column names
        cols = get_column_names(cursor)
        #store the rows in a dictionary by ticket so all of one ticket's changes are in one spot.
        # - then store by timestamp in a sub-dictionary so simultaneous changes to a ticket are one feed item
        # - this means that if people make changes to two different tickets simultaneously it won't be an issue
        # - because of the way that the query grabs the data, "title" and "id" will be the same for all changetime-colliding rows
        items = {}
        for row in cursor:
            rowAsDict = dict(zip(cols,row))
            
            if rowAsDict['id'] in items:
                if rowAsDict['changetime'] in items[rowAsDict['id']]:
                    #we've already got something at this time; append it to the changetime's value list
                    items[rowAsDict['id']][rowAsDict['changetime']].append(rowAsDict)
                else:
                    items[rowAsDict['id']][rowAsDict['changetime']] = [rowAsDict]
            else:
                items[rowAsDict['id']] = {rowAsDict['changetime']:[rowAsDict]}
        self.env.log.debug('Tickets in Feed: %s' % items.values())
        #because we're using our own template, we can just blow away the current data structure
        # - keep the report's title, and description, and, uh, report (report is a dictionary that has an id and a resource object pointing to the report)
        # - context lets us use wiki_to_html
        data = {'items':items,
                'title':data['title'],
                'description':data['description'],
                'report':data['report'],
                'context':data['context']}
        
        return ('detailedrss.rss',data,'application/rss+xml')        
