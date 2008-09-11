from trac.web.api import ITemplateStreamFilter
from trac.perm import IPermissionRequestor
from trac.core import *
from genshi.core import *
from genshi.builder import tag
from sets import Set as set
from genshi.filters.transform import Transformer
from blackmagic import *

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
                if (not req.perm.has_permission(perm) or perm == "ALWAYS"):
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
