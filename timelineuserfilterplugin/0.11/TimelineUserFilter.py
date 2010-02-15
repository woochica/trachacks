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
            if (req.args.has_key('inc_users')):
              inc_users = req.args['inc_users']
              
              # make value persistent...
              req.session['timeline.filter.inc_users'] = inc_users
            elif (req.session.has_key('timeline.filter.inc_users')):
              # use persistent value...
              inc_users = req.session['timeline.filter.inc_users']
            else:
              inc_users = ''

            if (req.args.has_key('exc_users')):
              exc_users = req.args['exc_users']
              
              # make value persistent...
              req.session['timeline.filter.exc_users'] = exc_users
            elif (req.session.has_key('timeline.filter.exc_users')):
              # use persistent value...
              exc_users = req.session['timeline.filter.exc_users']
            else:
              exc_users = ''

            if (inc_users!=''):
                # use defined filter... 
                inc_users = [user.strip() for user in inc_users.split(',')]
                filtered_events = []
                for event in data['events']:
                    if event['author'] in inc_users:
                        filtered_events.append(event)
                data['events'] = filtered_events
                
            if (exc_users!=''):
                # use defined filter... 
                exc_users = [user.strip() for user in exc_users.split(',')]
                filtered_events = []
                for event in data['events']:
                    if event['author'] not in exc_users:
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
        return tag.div(tag.label("Include users: ",
                                 tag.input(type="text",
                                           name="inc_users",
                                           value=req.session.get('timeline.filter.inc_users',''),
                                           style_="width:60%"
                                          )
                                )
                       +
                       tag.br()
                       +
                       tag.label("Exclude users: ",
                                 tag.input(type="text",
                                           name="exc_users",
                                           value=req.session.get('timeline.filter.exc_users',''),
                                           style_="width:60%"
                                          )
                                )
                      )                    
                                   
