from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script


class BetterHoursDisplay(Component):
    """This component changes decimal hours to hours/minutes"""
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script(req, "billing/ticket.js")
        return (template, data, content_type)

class HoursLayoutChanger(Component):
    """This moves the add hours box up to underneath the comment box.
    Removes the add_hours field from the ticket properties display 
    and then cleans up these tables

    This prevents needing to expand the "Modify Ticket" section to 
    add hours and a comment
    """
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script(req, "billing/change_layout.js")
        return (template, data, content_type)


class AddHoursSinceComment(Component):
    """Adds a button next to the changes in ticket history that fills
    the Add Hours box with the time since that change"""
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_script(req, "billing/add_hours_from_comment.js")
        return (template, data, content_type)


