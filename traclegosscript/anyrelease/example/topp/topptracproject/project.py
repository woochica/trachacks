from traclegos.project import TracProject
from paste.script import templates

var = templates.var

class ToppTracProject(TracProject):
    _template_dir = 'template'
    summary = 'The Open Planning Project Trac Template'

    vars = [ var('basedir', 'base directory for trac'),
             var('domain', 'domain name where this project is to be served', 
                 default='localhost'),
             var('footer', '',
                 default='Visit <a href="http://www.openplans.org/">The Open Planning Project</a>'),
             var('repository_url', 'URL of the SVN repository',
                 default='https://svn.openplans.org/svn')
             ]

    requirements = ['https://svn.openplans.org/svn/trac/install/plugins.txt']

