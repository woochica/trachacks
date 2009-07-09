from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.ticket.model import Ticket

from genshi.builder import tag
from genshi.filters import Transformer

author = "pdoup"

class TimelineComponentFilterPlugin(Component):
    """Filters ticket timeline events by component(s).
    """
       
    implements(IRequestFilter, ITemplateStreamFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'timeline.html':
            components = req.args.get('filter-components', '')
            if components:
                tickettypes = ["newticket", "editedticket", "closedticket", "attachment", "reopenedticket"]
                filtered_events = []
                for event in data['events']:
                    if event['kind'] in tickettypes:
                        resource = event['kind'] == "attachment" and event['data'][0].parent or event['data'][0]
                        if resource.realm == "ticket":
                            ticket = Ticket( self.env, resource.id )
                            if ticket.values['component'] in components:
                                filtered_events.append(event)
                    else:
                        filtered_events.append(event)
                data['events'] = filtered_events
        return (template, data, content_type)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'timeline.html':
            # Insert the new field for entering user names
            filter = Transformer('//form[@id="prefs"]/fieldset')
            return stream | filter.before(tag.br()) | filter.before(tag.label("Filter Components (none for all): ")) | filter.before(tag.br()) | filter.before(self._components_field_input(req))
        return stream

    def _components_field_input(self, req):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT name FROM component ORDER BY name")
        select = tag.select(name="filter-components", id="filter-components", multiple="multiple", size="10")
        selectedcomps = []
        selectedcomps = req.args.get('filter-components', '')
        for component in cursor:
            if component[0] in selectedcomps:
                select.append(tag.option(component[0], value=component[0], selected="selected"))
            else:
                select.append(tag.option(component[0], value=component[0]))
        return select
