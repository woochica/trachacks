# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from genshi.builder import tag
from genshi.filters.transform import Transformer
from genshi.input import HTML
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from operator import itemgetter

from simplemultiproject.model import *
from simplemultiproject.model import smp_filter_settings, smp_settings

class SmpRoadmapProjectFilter(Component):
    """Allows for filtering by 'Project'
    """
    
    implements(IRequestFilter, ITemplateStreamFilter)
    
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/roadmap'):
            filter_projects = smp_filter_settings(req, 'roadmap', 'projects')
                
            if filter_projects and len(filter_projects) > 0:
                milestones = data.get('milestones')
                milestones_stats = data.get('milestone_stats')
                
                filtered_milestones = []
                filtered_milestone_stats = []
        
                if milestones:
                    for idx, milestone in enumerate(milestones):
                        milestone_name = milestone.name
                        project = self.__SmpModel.get_project_milestone(milestone_name)
    
                        if project and project[0] in filter_projects:
                            filtered_milestones.append(milestone)
                            filtered_milestone_stats.append(milestones_stats[idx])
        
                    data['milestones'] = filtered_milestones
                    data['milestone_stats'] = filtered_milestone_stats
            
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename.startswith("roadmap"):
            filter_projects = smp_filter_settings(req, 'roadmap', 'projects')
            filter = Transformer('//form[@id="prefs"]/fieldset/div[1]')
            stream = stream | filter.before(tag.label("Filter Projects:")) | filter.before(tag.br()) | filter.before(self._projects_field_input(req, filter_projects)) | filter.before(tag.br())

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

class SmpRoadmapProject(Component):
    """Groups milestones by 'Project'
    """
    
    implements(IRequestFilter, ITemplateStreamFilter)
    
    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    def pre_process_request(self, req, handler):
        return handler

    def __extract_milestones_array(self,stream_name_milestones):
        names_milestone = str(stream_name_milestones)
        edits = [('<em>', ';'), ('</em>', ';')]
        for search, replace in edits:
            names_milestone = names_milestone.replace(search, replace)
        names_milestone = names_milestone.replace(';;', ',')
        names_milestone = names_milestone.replace(';', '')
        array_milestones = names_milestone.split(',')

        return array_milestones

    def __extract_div_milestones_array(self,tag_milestone,stream_milestones):
        html_milestones = str(stream_milestones)
        ini_index = html_milestones.find(tag_milestone)
        divarray = []
        ocurrencia = True
        while (ocurrencia):
            end_index = html_milestones.find(tag_milestone, ini_index + len(tag_milestone))
            if(end_index < 0):
                divarray.append(html_milestones[ini_index:len(html_milestones)])
                ocurrencia = False
            else:
                divarray.append(html_milestones[ini_index:end_index])
                ini_index = end_index
        return divarray

    def __process_div_projects_milestones(self,milestones,div_milestones_array):
        project = self._map_milestones_to_projects(milestones)

        div_projects_milestones = ''
        
        for a in sorted(project.keys()):
            if(a == "--None Project--"):
                div_project = '<br><div id="project"><fieldset><legend><b>None Project</b></legend>'
            else:
                div_project = '<br><div id="project"><fieldset><legend><b>Project: <em>%s</em></b></legend>' % a
            div_milestone = ''
            
            if len(project[a]) > 0:
                for b in project[a]:
                    mi = '<em>%s</em>' % b
                    for i in range(len(div_milestones_array)):
                        if(div_milestones_array[i].find(mi)>0):
                            div_milestone = div_milestone + div_milestones_array[i]
                div_project = div_project + to_unicode(div_milestone) + '</fieldset></div>'
                div_projects_milestones = to_unicode(div_projects_milestones + div_project)

        stream_div_projects_milestones = HTML(div_projects_milestones)
        return stream_div_projects_milestones
        
    def _map_milestones_to_projects(self, milestones):
        project = {}
        for milestone in milestones:
            project_id = self.__SmpModel.get_project_milestone(milestone)
            
            if project_id == None:
                project_id = self.__SmpModel.get_project_version(milestone)
            
            if project_id == None:
                if project.has_key("--None Project--"):
                    project["--None Project--"].append(milestone)
                else:
                    project["--None Project--"] = [milestone]
            else:
                if project.has_key(project_id[0]):
                    project[project_id[0]].append(milestone)
                else:
                    project[project_id[0]] = [milestone]
        
        return project

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename.startswith("roadmap"):
            stream_roadmap = HTML(stream)
            stream_milestones = HTML(stream_roadmap.select('//div[@class="roadmap"]/div[@class="milestones"]'))
            
            milestones = self.__extract_milestones_array(stream_milestones.select('//div[@class="milestone"]/div/h2/a/em'))
            div_milestones_array = self.__extract_div_milestones_array('<div class="milestone">',stream_milestones)
            
            div_projects_milestones = self.__process_div_projects_milestones(milestones, div_milestones_array)
            
            return stream_roadmap | Transformer('//div[@class="roadmap"]/div[@class="milestones"]').replace(div_projects_milestones)

        return stream

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type  
