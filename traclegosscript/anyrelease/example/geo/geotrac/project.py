from traclegos.project import TracProject
from paste.script import templates

var = templates.var

class GeoTracProject(TracProject):
    _template_dir = 'template'
    summary = 'Geo Trac project template'

    vars = [ var('basedir', 'base directory for trac',
                 default='.'),
             var('domain', 'domain name where this project is to be served', 
                 default='localhost'),
             ]

