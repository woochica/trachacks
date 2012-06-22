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
from operator import itemgetter

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
            all_projects   = [project[1] for project in sorted(self.__SmpModel.get_all_projects(), key=itemgetter(1))]
            component_projects = {}
            components = []
            project_versions = {}

            for comp in all_components:
                components.append(comp.name)
                comp_projects = [project[0] for project in sorted(self.__SmpModel.get_projects_component(comp.name), key=itemgetter(0))]
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
            
            self._add_milestones_maps(req, data['ticket'])

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html":
            # replace "project" text input (lineedit) for ticket editing with a selection field
            filter = Transformer('//input[@id="field-project"]')
            ticket_data = data['ticket']

            script_filter = Transformer('//div[@id="banner"]')

            stream = stream | filter.replace(self._projects_field_ticket_input(req, ticket_data))
            stream = stream | script_filter.before(self._update_milestones_script(req))

        return stream

    def _update_milestones_script(self, req):
        script = tag.script(type="text/javascript", src=req.href.chrome("simplemultiproject", "filter_milestones.js"))
        return script

    def _add_milestones_maps(self, req, ticket_data):

        milestone = ticket_data.get_value_or_default('milestone')
        project   = ticket_data.get_value_or_default('project')

        allProjects = self.__SmpModel.get_all_projects()

        initialProjectMilestone = [ project, milestone ]
        milestonesForProject = {}
        milestonesForProject[""] = { "Please, select a project!": "" }

        for project in sorted(allProjects, key=itemgetter(1)):
            milestones = self.__SmpModel.get_milestones_of_project(project[1])
            milestonesForProject[project[1]] = { "": "" }
            for milestone in sorted(milestones, key=itemgetter(0)):
                milestonesForProject[project[1]][milestone[0]] = milestone[0]

        smp_milestonesForProject = { 'smp_milestonesForProject' : milestonesForProject }
        smp_initialProjectMilestone = { 'smp_initialProjectMilestone' : initialProjectMilestone }

        add_script_data(req, smp_initialProjectMilestone)
        add_script_data(req, smp_milestonesForProject)

    def _projects_field_ticket_input(self, req, ticket_data):
        all_projects = [project[1] for project in sorted(self.__SmpModel.get_all_projects(), key=itemgetter(1))]
        select = tag.select(name="field_project", id="field-project", onchange="smp_onProjectChange(this.value)")
        
        cur_project = ticket_data.get_value_or_default('project')

        select.append(tag.option("", value=""))
        for project in all_projects:
            if cur_project and project == cur_project:
                select.append(tag.option(project, value=project, selected="selected"))
            else:
                select.append(tag.option(project, value=project))
        return select
