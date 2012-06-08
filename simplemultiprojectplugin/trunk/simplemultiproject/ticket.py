# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#

from genshi.builder import tag
from genshi.filters.transform import Transformer
from simplemultiproject.model import *
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import ITemplateStreamFilter

class SmpTicketProject(Component):
    
    implements(ITemplateStreamFilter)
    
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html":
            # replace "project" text input (lineedit) for ticket editing with a selection field
            filter = Transformer('//input[@id="field-project"]')
            ticket_data = data['ticket']

            script_filter = Transformer('//div[@id="banner"]')

            stream = stream | filter.replace(self._projects_field_ticket_input(req, ticket_data))
            stream = stream | script_filter.before(self._update_milestones_maps(req, ticket_data))
            stream = stream | script_filter.before(self._update_milestones_script(req))

        return stream

    def _update_milestones_script(self, req):
        script = tag.script(type="text/javascript", src=req.href.chrome("simplemultiproject", "filter_milestones.js"))
        return script

    def _update_milestones_maps(self, req, ticket_data):

        milestone = ticket_data.get_value_or_default('milestone')
        project   = ticket_data.get_value_or_default('project')

        allProjects = self.__SmpModel.get_all_projects()

        jsVar = 'var smp_initialProjectMilestone = [ "%s" , "%s" ]; ' % (project, milestone)
        jsVar = to_unicode('%s var smp_milestonesForProject = { "" : { "Please, select a project!"  : "" }') % jsVar

        for project in allProjects:
            jsVar = '%s, "%s" : { "" : ""' % (jsVar, project[1])
            milestones = self.__SmpModel.get_milestones_of_project(project[1])

            for milestone in milestones:
                jsVar = '%s, "%s" : "%s"' % (jsVar, milestone[0], milestone[0])
    
            jsVar = '%s }' % jsVar

        jsVar = '%s };' % jsVar
            
        script = tag.script(jsVar, type="text/javascript")
        return script

    def _projects_field_ticket_input(self, req, ticket_data):
        cursor = self.__SmpModel.get_all_projects()
        select = tag.select(name="field_project", id="field-project", onchange="smp_onProjectChange(this.value)")
      
        db = self.env.get_db_cnx()
        cursor2 = db.cursor()

        project = ticket_data.get_value_or_default('project')

        #select.append(tag.option(row[0], value=row[0]))
        select.append(tag.option("", value=""))
        for component in cursor:
            if project and component[1] == project:
                select.append(tag.option(component[1], value=component[1], selected="selected"))
            else:
                select.append(tag.option(component[1], value=component[1]))
        return select
