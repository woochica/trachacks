from traclegos.project import TracProject
from paste.script import templates

var = templates.var

class OSSTracProject(TracProject):
    _template_dir = 'template'
    summary = 'Open Source Software project trac template'

    vars = [ var('basedir', 'base directory for trac',
                 default='.'),
             var('domain', 'domain name where this project is to be served', 
                 default='localhost'),
             ]

