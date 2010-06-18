from trac.web.api import ITemplateStreamFilter
from trac.perm import IPermissionRequestor
from trac.core import *
from genshi.core import *
from genshi.builder import tag

from genshi.filters.transform import Transformer
from blackmagic import *
from trac.ticket.query import QueryModule

from StringIO import StringIO
import csv
from trac.mimeview.api import Context
from trac.resource import Resource

import sys 
if sys.version_info < (2, 4, 0): 
    from sets import Set as set

## MONKEY PATCH THE QUERY MODULE CSV EXPORT FN TO ENFORCE PERMISSIONS
def new_csv_export(self, req, query, sep=',', mimetype='text/plain'):
    self.log.debug("T&E plugin has overridden QueryModule.csv_export so to enforce field permissions")

    ## find the columns that should be hidden
    hidden_fields = []
    fields = self.config.getlist(csection, 'fields', [])
    self.log.debug('QueryModule.csv_export: found : %s' % fields)
    for field in fields:
        perms = self.config.getlist(csection, '%s.permission' % field, [])
        #self.log.debug('QueryModule.csv_export: read permission config: %s has %s' % (field, perms))
        for (perm, denial) in [s.split(":") for s in perms] :
            perm = perm.upper()
            #self.log.debug('QueryModule.csv_export: testing permission: %s:%s should act= %s' %
            #               (field, perm, (not req.perm.has_permission(perm) or perm == "ALWAYS")))
            if (not req.perm.has_permission(perm) or perm == "ALWAYS") and denial.lower() in ["remove","hide"]:
                hidden_fields.append(field)
    ## END find the columns that should be hidden
    
    content = StringIO()
    cols = query.get_columns()
    writer = csv.writer(content, delimiter=sep)
    writer = csv.writer(content, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([unicode(c).encode('utf-8') for c in cols if c not in hidden_fields])
    
    context = Context.from_request(req)
    results = query.execute(req, self.env.get_db_cnx())
    self.log.debug('QueryModule.csv_export: hidding columns %s' %  hidden_fields)
    for result in results:
        ticket = Resource('ticket', result['id'])
        if 'TICKET_VIEW' in req.perm(ticket):
            values = []
            for col in cols:
                if col not in hidden_fields:
                    value = result[col]
                    if col in ('cc', 'reporter'):
                        value = Chrome(self.env).format_emails(context(ticket),
                                                               value)
                    values.append(unicode(value).encode('utf-8'))
            writer.writerow(values)
    return (content.getvalue(), '%s;charset=utf-8' % mimetype)

QueryModule.export_csv = new_csv_export

class TicketFormatFilter(Component):
    """Filtering the streams to alter the base format of the ticket"""
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("TicketFormatFilter executing") 
        if not filename == 'ticket.html':
            self.log.debug("TicketFormatFilter not the correct template")
            return stream
        
        self.log.debug("TicketFormatFilter disabling totalhours and removing header hours")
        stream = disable_field(stream, "totalhours")
        stream = remove_header(stream, "hours")
        return stream 


class QueryColumnPermissionFilter(Component):
    """ Filtering the stream to remove """
    implements(ITemplateStreamFilter)    
    
    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if not filename == "query.html":
            self.log.debug('Not a query returning')
            return stream

        def make_col_helper(field):
            def column_helper (column_stream):
                s =  Stream(column_stream)
                val = s.select('//input/@value').render()
                if val.lower() != field.lower(): #if we are the field just skip it
                    #identity stream filter
                    for kind, data, pos in s:
                        yield kind, data, pos        
            return column_helper

        fields = self.config.getlist(csection, 'fields', [])
        for field in fields:
            self.log.debug('found : %s' % field)
            perms = self.config.getlist(csection, '%s.permission' % field, [])
            self.log.debug('read permission config: %s has %s' % (field, perms))
            for (perm, denial) in [s.split(":") for s in perms] :
                perm = perm.upper()
                self.log.debug('testing permission: %s:%s should act= %s' %
                               (field, perm, (not req.perm.has_permission(perm) or perm == "ALWAYS")))
                if (not req.perm.has_permission(perm) or perm == "ALWAYS") and denial.lower() in ["remove","hide"]:
                    # remove from the list of addable 
                    stream = stream | Transformer(
                        '//select[@id="add_filter"]/option[@value="%s"]' % field
                        ).replace(" ")

                    # remove from the list of columns
                    stream = stream | Transformer(
                        '//fieldset[@id="columns"]/div/label'
                        ).filter(make_col_helper(field))
                    
                    #remove from the results table
                    stream = stream | Transformer(
                        '//th[@class="%s"]' % field
                        ).replace(" ")
                    stream = stream | Transformer(
                        '//td[@class="%s"]' % field
                        ).replace(" ")

                    # remove from the filters
                    stream = stream | Transformer(
                        '//tr[@class="%s"]' % field
                        ).replace(" ")

                    
        return stream
