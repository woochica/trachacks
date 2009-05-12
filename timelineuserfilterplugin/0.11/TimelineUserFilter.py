from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters import Transformer

author = "daveappendix"

class TimelineUserFilterPlugin(Component):
    """Filters timeline events by user.
    """
       
    implements(IRequestFilter, ITemplateStreamFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'timeline.html':
            users = req.args.get('users', '')
            if users:
                users = [user.strip() for user in users.split(',')]
                filtered_events = []
                for event in data['events']:
                    if event['author'] in users:
                        filtered_events.append(event)
                data['events'] = filtered_events
        return (template, data, content_type)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'timeline.html':
            # Insert the new field for entering user names
            filter = Transformer('//form[@id="prefs"]/fieldset')
            return stream | filter.before(self._user_field_input(req))
        return stream

    def _user_field_input(self, req):
        return tag.label("Filter users: ",
                         tag.input(type="text",
                                   name="users",
                                   value=req.args.get('users', ''),
                                   style_="width:60%"))
