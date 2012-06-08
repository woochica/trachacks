# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#

from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.ticket.model import Ticket
from simplemultiproject.model import *
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from operator import itemgetter

class SmpTimelineProjectFilter(Component):
    """Allows for filtering by 'Project'
    """
    
    implements(IRequestFilter, ITemplateStreamFilter)
    
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if template == 'timeline.html':
            filter_projects = self._filtered_projects(req) 
            
            if filter_projects:               
                filtered_events = []
                tickettypes = ("newticket", "editedticket", "closedticket", "attachment", "reopenedticket")
                for event in data['events']:
                    if event['kind'] in tickettypes:
                        resource = event['kind'] == "attachment" and event['data'][0].parent or event['data'][0]
                        if resource.realm == "ticket":
                            ticket = Ticket( self.env, resource.id )               
                            if ticket.get_value_or_default('project') in filter_projects:
                                filtered_events.append(event)
                        
                    else:
                        filtered_events.append(event)
    
                data['events'] = filtered_events

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'timeline.html':
            filter_projects = self._filtered_projects(req) 

            filter = Transformer('//form[@id="prefs"]/div[1]')
            stream = stream | filter.before(tag.label("Filter Projects:")) | filter.before(tag.br()) | filter.before(self._projects_field_input(req, filter_projects)) | filter.before(tag.br()) | filter.before(tag.br())

        return stream

    # Internal

    def _projects_field_input(self, req, selectedcomps):
        cursor = self.__SmpModel.get_all_projects()

        select = tag.select(name="filter-projects", id="filter-projects", multiple="multiple", size="10")
        select.append(tag.option("All", value="All"))
        
        for component in sorted(cursor, key=itemgetter(1)):
            project = to_unicode(component[1])
            if selectedcomps and project in selectedcomps:
                select.append(tag.option(project, value=project, selected="selected"))
            else:
                select.append(tag.option(project, value=project))
        return select
        
    def _filtered_projects(self, req):
        filtered_projects = req.args.get('filter-projects')
        filtered_projects = type(filtered_projects) is unicode and (filtered_projects,) or filtered_projects

        # check session attribtes
        if not filtered_projects:
            if req.session.has_key('timeline.filter.projects'):
                filtered_projects = to_unicode(req.session['timeline.filter.projects'])
        else:
            req.session['timeline.filter.projects'] = filtered_projects

        if filtered_projects and u'All' in filtered_projects:
            filtered_projects = None

        return filtered_projects
