import os
import shutil
from paste.script import templates

var = templates.var

class TracProjectTemplate(templates.Template):
    _template_dir = 'template'
    summary = 'templatize configuration for a trac project'
    vars = [
        var('file', 'file or project to templatize'),
        var('description', 'One-line description of the package'),
        ] 

    def pre(self, command, output_dir, vars):
        pass

    def post(self, command, output_dir, vars):
        if os.path.exists(vars['file']):
            shutil.copy(vars['file'], 
                        os.path.join(output_dir, 
                                     vars['package'],
                                     'template',
                                     'conf'))

