"""
collection of project templates
"""

import ConfigParser

from paste.script.templates import var
from traclegos.config import ConfigMunger
from traclegos.pastescript.string import PasteScriptStringTemplate
from traclegos.pastescript.var import vars2dict, dict2vars
from traclegos.project import project_dict
from traclegos.project import TracProject

from StringIO import StringIO

class ProjectTemplates(object):
    """class handling a group of templates of mixed type"""

    def __init__(self, *templates):
        self.templates = templates
        self.resolve()

    def append(self, *templates):
        """append templates to the configuraton"""
        self.templates += templates
        if hasattr(self, '_configuration'):
            del self._configuration
        self.resolve()

    def __iadd__(self, templates):
        self.append(*templates)

    def resolve(self):
        """determine pastescript templates and .ini files"""
        project_types = project_dict()
        inifiles = []
        pastescript_templates = []
        for template in self.templates:
            proj = None
            if isinstance(template, TracProject):
                proj = template
            if isinstance(template, basestring):
                proj = project_types.get(template)
            if proj:
                inifile = proj.inifile()
                if inifile:
                    inifiles.append(inifile)
                pastescript_templates.append(proj)
            else:
                inifiles.append(template)
        self.pastescript_templates = pastescript_templates
        self.inifiles = inifiles

    def vars(self, vars=()):
        """return a dictionary of PasteScript vars"""
        optdict = {}
        for template in self.pastescript_templates:
            vars2dict(optdict, *template.vars)
        vars2dict(optdict, *vars)
        return optdict

    def options(self, vars=()):
        """return all PasteScript vars including those from the template"""
        optdict = dict((missed, var(missed, '')) for missed in self.missing())
        optdict.update(self.vars(vars))
        return optdict

    def configuration(self):
        """returns string of uninterpolated configuration"""

        if not hasattr(self, '_configuration'):
            # could just do this on __init__ (or resolve)
            munger = ConfigMunger()
            try:
                munger.read(*self.inifiles)
            except ConfigParser.MissingSectionHeaderError, e:
                # this probably means a bad URI
                raise IOError('Resource not found: %s' % e.line)

            config = StringIO()
            munger.write(config)
            self._configuration = config.getvalue()

        return self._configuration

    def missing(self, vars=None):
        if vars is None:
            vars = {}
        if not hasattr(self, 'template'):
            self.template = PasteScriptStringTemplate(self.configuration())
        return self.template.missing(vars)

    def interpolate_configuration(self, vars):
        """
        return configuration (trac.ini) as a string 
        interpolated with the vars dictionary
        """
        assert not self.missing(vars)
        return self.template.substitute(**vars)

    def options_tuples(self, vars):
        """return the tuples for the configuration"""
        # create a new munger with the interpolated configuration
        munger = ConfigMunger()
        munger.read(self.interpolate_configuration(vars))
        return munger.tuples()

