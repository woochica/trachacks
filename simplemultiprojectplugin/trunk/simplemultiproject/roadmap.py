# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from genshi.filters.transform import Transformer
from genshi.input import HTML
from simplemultiproject.model import *
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter

class SmpRoadmapProject(Component):
    
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
        project = {}
        for milestone in milestones:
            project_id = self.__SmpModel.get_project_milestone(milestone)
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
        
        div_projects_milestones = ''
        for a in project.keys():
            if(a == "--None Project--"):
                div_project = '<br><div id="project"><fieldset><legend><b>None Project</b></legend>'
            else:
                div_project = '<br><div id="project"><fieldset><legend><b>Project: <em>%s</em></b></legend>' % a
            div_milestone = ''
            for b in project[a]:
                mi = '<em>%s</em>' % b
                for i in range(len(div_milestones_array)):
                    if(div_milestones_array[i].find(mi)>0):
                        div_milestone = div_milestone + div_milestones_array[i]
            div_project = div_project + div_milestone + '</fieldset></div>'
            div_projects_milestones = div_projects_milestones + div_project
        stream_div_projects_milestones = HTML(div_projects_milestones)
        return stream_div_projects_milestones
        
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "roadmap.html":
            stream_roadmap = HTML(stream)
            stream_milestones = HTML(stream_roadmap.select('//div[@class="roadmap"]/div[@class="milestones"]'))
            
            milestones = self.__extract_milestones_array(stream_milestones.select('//div[@class="milestone"]/div/h2/a/em'))
            div_milestones_array = self.__extract_div_milestones_array('<div class="milestone">',stream_milestones)
            
            div_projects_milestones = self.__process_div_projects_milestones(milestones, div_milestones_array)
                        
            return stream_roadmap | Transformer('//div[@class="roadmap"]/div[@class="milestones"]').replace(div_projects_milestones)
        
        return stream

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type    