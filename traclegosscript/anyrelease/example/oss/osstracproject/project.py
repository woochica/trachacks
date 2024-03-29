import os

from traclegos.project import TracProject
from paste.script import templates

var = templates.var

class OSSTracProject(TracProject):
    _template_dir = 'template'
    summary = 'Open Source Software Trac project template'

    vars = [ var('basedir', 'base directory for trac',
                 default='.'),
             var('domain', 'domain name where this project is to be served', 
                 default='localhost'),
             var('description', 'description of the trac project',
                 default=''),
             var('manager', 'email address of the Trac manager', default=''),
             var('logo', '', default=''),
             var('url', 'url', default=''),
             var('footer', 'footer', default=''),
             var('favicon', 'favicon', default=''),
             var('repository_url', 'base url of SVN repository', default=''),
             var('repository_dir', 'directory of SVN repository', default='')
             ]


    def pre(self, command, output_dir, vars):
        TracProject.pre(self, command, output_dir, vars)
        vars['basedir'] = os.path.realpath(vars['basedir'])
