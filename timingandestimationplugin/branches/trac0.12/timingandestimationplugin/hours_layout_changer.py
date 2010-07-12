from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script

class HoursLayoutChanger(Component):
    """This moves the add hours box up to underneath the comment box. 
    This prevents needing to expand the "Modify Ticket" section to 
    add hours and a comment
    """
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script(req, "Billing/change_layout.js")
        return (template, data, content_type)
 

class TicketPropsLayoutChanger(Component):
    """This removes extra whitespace rendered to the ticket properties box
    """
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script(req, "Billing/whitespace_remover.js")
        return (template, data, content_type)
 
