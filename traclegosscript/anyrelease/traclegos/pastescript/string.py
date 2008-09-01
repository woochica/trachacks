#!/usr/bin/env python
"""
using pastescript template from a string
"""

import os
import re
import shutil
import tempfile

from paste.script.copydir import LaxTemplate
from paste.script.templates import Template
from traclegos.pastescript.command import create_distro_command

class PasteScriptStringTemplate(Template):

    def __init__(self, string, name=None, summary='', interactive=False, 
                 vars=None):

        self.string = string
        self.cmd = create_distro_command(interactive)

        # make a temporary directory + file for the string
        directory = tempfile.mkdtemp()
        if not name:
            name = tempfile.mktemp(dir=directory)
        fd = file(os.path.join(directory, name), 'w')
        print >> fd, string
        fd.close()
        self.name = name

        # variables for PasteScript's template
        Template.__init__(self, name)
        self._template_dir = directory
        self.summary = summary
        self.vars = vars or []

    def __del__(self):
        shutil.rmtree(self._template_dir)

    def interpolate(self, vars=None, interactive=False, fp=None):
        """return the interpolated string"""

        vars = vars or {}
        directory = tempfile.mkdtemp()
        self.run(self.cmd, directory, vars)
        string = file(os.path.join(directory, self.name)).read()
        shutil.rmtree(directory)
        return string

    def substitute(self, **vars):
        return LaxTemplate(self.string).safe_substitute(vars)

    def missing(self, vars=()):
        return set([ i[2] for i in re.findall(LaxTemplate.pattern, self.string)
                     if i[2] and i[2] not in vars ])

if __name__ == '__main__':
    import sys
    template = StringTemplate(' '.join(sys.argv[1:]))
    result = template.interpolate()
    print result
        
