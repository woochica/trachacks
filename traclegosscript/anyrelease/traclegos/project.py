#!/usr/bin/env python
"""
definition of a trac project
"""

import os
import pkg_resources
import subprocess
from paste.script import templates
from traclegos.db import available_databases

class TracProject(templates.Template):
    """a trac project"""
    # eventually this class should do most if not all of what TracLegos
    # does and its functionality should be factored to that end
    # methodologies for doing so:

    # * container: self.project_creator = TracLegos(...): this method favors
    # keeping TracLegos as the canonical project factory which is called via
    # the command line and via `paster create` or TTW

    # * deprecator: the functionalities of TracLegos are mostly (if not 
    # entirely) moved into this class and TracLegos becomes a front-end for
    # the TracProject PasteScript template (assuming it needs to exist)
    
    # practicalities going forward should determine which of these 
    # methodologies is favored

    # PoachEggs requirements files for the template
    requirements = [] # XXX deprecated?

    # Trac permissions for the template
    permissions = {}

    # database to be used
    db = None

    ### attrs for PasteScript Template
    
    def pre(self, command, output_dir, vars):
        pass

    def post(self, command, output_dir, vars):
        pass

    ### internal methods

    def inifile(self):
        """
        returns the path to the trac.ini template associated with this TracProject
        (if any)
        """        
        files = [ 'trac.ini_tmpl', 'trac.ini' ]
        for f in files:
            filename = os.path.join(self.template_dir(), 'conf', f)
            if os.path.exists(filename):
                return filename

    def database(self):
        if self.db is None:
            return self.db
        if isinstance(self.db, basestring):
            return available_databases()[self.db]
        return self.db()
            

def projects():
    """return TracProject templates installed as eggs"""
    templates = []
    for entry_point in pkg_resources.iter_entry_points('paste.paster_create_template'):
        try:
            template = entry_point.load()
        except:
            continue
        if issubclass(template, TracProject):
            templates.append(template(entry_point.name))
    return templates

def project_dict():
    return dict((template.name, template) for template in projects())

if __name__ == '__main__':
    from traclegos.project import TracProject
    templates = project_dict()
    for name, template in templates.items():
        print name, template

    template.inifile()
