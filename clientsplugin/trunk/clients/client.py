# -*- coding: utf-8 -*-
from trac.core import *
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer 

from clients import model
from StringIO import StringIO

class ClientModule(Component):
    """Allows for tickets to be assigned to particular clients."""
    
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        # Some ticket views do not actually load the data in this way
        # e.g. action=history or action=diff
        if not data or not data.has_key('fields'):
            return template, data, content_type

        newticket = req.path_info.startswith('/newticket')
        if req.path_info.startswith('/ticket/') or newticket:
            for field in data['fields']:
                if 'client' == field['name']:
                    field['type'] = 'select'
                    field['options'] = []
                    for client in model.Client.select(self.env):
                        field['options'].append(client.name)
                    if newticket:
                        default_client = self.config.get('ticket', 'default_client')
                        if default_client:
                            data['ticket']['client'] = default_client
                    break;
        elif req.path_info.startswith('/query'):
            if data['fields'].has_key('client'):
                data['fields']['client']['type'] = 'select'
                data['fields']['client']['options'] = []
                for client in model.Client.select(self.env):
                    data['fields']['client']['options'].append(client.name)
        return template, data, content_type
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        # Add Stylesheet here, so that the ticket page gets it too :)
        add_stylesheet(req, "clients/clients.css")

        newticket = req.path_info.startswith('/newticket')
        if req.path_info.startswith('/ticket/') or newticket:
            setdefaultrate = ''
            if newticket:
              setdefaultrate = "$('#field-client').trigger('change');"
            
            script = StringIO()
            script.write("""
              $(document).ready(function() {
                $('#field-client').change(function() {
                  """);
            script.write('var clientrates = new Array();')
            for client in model.Client.select(self.env):
                script.write('clientrates["%s"] = %s;' % (client.name, client.default_rate or '""'))
            script.write("""
                  try { $('#field-clientrate').attr('value', clientrates[this.options[this.selectedIndex].value]); }
                  catch (er) { }
                });
                %s
             });""" % setdefaultrate);
            stream |= Transformer('.//head').append(tag.script(script.getvalue(), type_='text/javascript'))
        return stream
    
    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('clients', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
    
    def validate_ticket(self, req, ticket):
        # Todo validate client is valid
        pass
        #if req.args.get('action') == 'resolve':
        #    links = TicketLinks(self.env, ticket)
        #    for i in links.blocked_by:
        #        if Ticket(self.env, i)['status'] != 'closed':
        #            yield None, 'Ticket #%s is blocking this ticket'%i

