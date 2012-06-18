# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#

from genshi.builder import tag
from genshi.filters.transform import Transformer
from simplemultiproject.model import *
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import add_script, add_script_data
from trac.ticket import model

class SmpTicketProject(Component):
    
    implements(IRequestFilter, ITemplateStreamFilter)
    
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            all_components = model.Component.select(self.env)
            all_projects   = [project[1] for project in self.__SmpModel.get_all_projects()]
            component_projects = {}
            components = []
            project_versions = {}

            for comp in all_components:
                components.append(comp.name)
                comp_projects = [project[0] for project in self.__SmpModel.get_projects_component(comp.name)]
                if comp_projects and len(comp_projects) > 0:
                    component_projects[comp.name] = comp_projects

            all_projects2 = all_projects
            for project in all_projects2:
                project_versions[project] = ['']
                project_versions[project].extend([version[0] for version in self.__SmpModel.get_versions_of_project(project)])
                
            projects = { 'smp_all_projects': all_projects }
            component_projects = { 'smp_component_projects': component_projects }
            all_components = { 'smp_all_components': components }
            def_component = { 'smp_default_component': data.get('ticket').get_value_or_default('component') }
            def_version = { 'smp_default_version': data.get('ticket').get_value_or_default('version') }
            project_versions = { 'smp_project_versions': project_versions }

            add_script_data(req, projects)
            add_script_data(req, all_components)
            add_script_data(req, component_projects)
            add_script_data(req, def_component)
            add_script_data(req, def_version)
            add_script_data(req, project_versions)

        return template, data, content_type

    # ITemplateStreamFilter methods

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
