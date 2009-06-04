#!/usr/bin/env python
"""
driver to create trac projects --
the head of the octopus
"""

import inspect
import os
import sys

from martini.config import ConfigMunger
from optparse import OptionParser
from paste.script.templates import var
from paste.script.templates import Template
from trac.admin.console import TracAdmin
from trac.core import TracError
from trac.env import Environment
from traclegos.admin import TracLegosAdmin
from traclegos.db import available_databases
from traclegos.db import SQLite
from traclegos.pastescript.command import create_distro_command
from traclegos.pastescript.string import PasteScriptStringTemplate
from traclegos.pastescript.var import vars2dict, dict2vars
from traclegos.project import project_dict
from traclegos.project import TracProject
from traclegos.repository import available_repositories
from traclegos.templates import ProjectTemplates
from StringIO import StringIO

# TODO: warn about duplicate variables or options (optionally)

class TracLegos(object):
    """tool for assembling trac projects from building blocks"""

    # global options -- these should apply to any trac instance
    # XXX maybe these should move to TracProject
    # (like so many other things)
    options = [ var('project', 'name of project'),
                var('directory', 'directory for trac projects'),
                var('description', 'description of the trac project'),
                var('url', 'alternate url for project'),
                var('favicon', 'favicon for the project')
                ]

    interactive = True

    def __init__(self, directory, master=None, inherit=None, 
                 site_templates=None, vars=None, options=()):
        """
        * directory: directory for project creation
        * master: path to master trac instance
        * inherit: inherited configuration to update
        * site_templates: global site configuration used for all projects
        * vars: values of variables for interpolation 
        * options: descriptions and annotations on variables
        """

        self.directory = directory
        assert self.directory # must have a directory to work in!
        self.site_templates = site_templates or []
        self.vars = { 'url': '', 'favicon': ''}
        self.vars.update(vars or {})
        self.master = master
        self.inherit = inherit or master or None
        self.options.extend(options)

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        self.vars['directory'] = self.directory

    ### utility functions

    @classmethod
    def arguments(cls):
        """
        returns a dictionary arguments to the constructor, __init__, 
        and their defaults or None for required arguments
        """
        argspec = inspect.getargspec(cls.__init__)
        args = dict([(i, None) for i in argspec[0][1:]])
        args.update(dict(zip(argspec[0][len(argspec[0])- len(argspec[-1]):], 
                             argspec[-1])))
        return args

    def project_templates(self, templates):
        # apply site configuration last (override)
        return ProjectTemplates(*(templates + self.site_templates))
    
    def repository_fields(self, project):
        """
        arguments to RepositorySetup.setup that may be interpolated 
        from variables
        """
        return { 'SVNSync': {'repository_dir': os.path.join(self.directory, project, 'mirror') },
                 'NewSVN': {'repository_dir': os.path.join(self.directory, project, 'svn') },
                 'NoRepository': { 'repository_dir': '' },
                 }

    def create_project(self, project, templates, vars=None,
                       database=None, repository=None,
                       return_missing=False):
        """
        * project: path name of project
        * templates: templates to be applied on project creation
        * vars: variables for interpolation
        * database:  type of database to use
        * repository: type of repository to use
        """
        
        ### set variables

        dirname = os.path.join(self.directory, project)
        _vars = vars or {}
        vars = self.vars.copy()
        vars.update(_vars)
        vars['project'] = project        

        ### munge configuration

        # get templates

        # XXX hack to get the specified DB out of pastescript templates
        if not database:
            if isinstance(templates, ProjectTemplates):
                pastescript_templates = templates.pastescript_templates
            else:
                pastescript_templates = ProjectTemplates(*(templates + self.site_templates)).pastescript_templates
            databases = set([ template.database() for template in pastescript_templates
                              if template.db is not None])
            if databases:
                assert len(databases) == 1
                database = databases.pop()
        if not database:
            database = SQLite()

        _templates = []
        _templates.append(database.config())
        if repository:
            _templates.append(repository.config())

        if isinstance(templates, ProjectTemplates):
            if _templates:
                templates.append(*_templates)
        else:
            templates += _templates
            templates = self.project_templates(templates)

        # determine the vars/options
        optdict = templates.vars(self.options)
        repo_fields = {}
        if database:
            vars2dict(optdict, *database.options)
        if repository:
            vars2dict(optdict, *repository.options)
            repo_fields = self.repository_fields(project).get(repository.name, {})

        ### interpolate configuration

        command = create_distro_command(interactive=self.interactive)
        
        # check for missing variables
        missing = templates.missing(vars)
        missing.update(set(optdict.keys()).difference(vars.keys()))
        if return_missing:
            return missing
        if missing:

            # use default repo fields if they are missing
            for field in repo_fields:
                if field in missing:
                    vars[field] = repo_fields[field]
                    missing.remove(field)

            # add missing variables to the optdict
            for missed in missing:
                if missed not in optdict:
                    optdict[missed] = var(missed, '')

            if missing:
                paste_template = Template(project)
                paste_template._read_vars = dict2vars(optdict) # XXX bad touch
                paste_template.check_vars(vars, command)
        

        ### create the database
        if database:
            database.setup(**vars)
        
        ### create the trac environment
        options = templates.options_tuples(vars)
        options.append(('project', 'name', project)) # XXX needed?
        if self.inherit:
            options.append(('inherit', 'file', self.inherit))
        env = Environment(dirname, create=True, options=options)

        ### repository setup
        if repository:
            repository.setup(**vars)
            try:
                repos = env.get_repository()
                repos.sync()
            except TracError:
                pass

        ### read the generated configuration 
        _conf_file = os.path.join(dirname, 'conf', 'trac.ini')
        fp = file(_conf_file)
        _conf = fp.read()
        fp.close()

        ### run pastescript templates
        command.interactive = False
        for paste_template in templates.pastescript_templates:
            paste_template.run(command, dirname, vars)

        # write back munged configuration 
        munger = ConfigMunger(_conf, options)
        fp = file(_conf_file, 'w')
        munger.write(fp)
        fp.close()

        # TODO: update the inherited file:
        # * intertrac

        # trac-admin upgrade the project
        env = Environment(dirname)
        if env.needs_upgrade():
            env.upgrade()

        ### trac-admin operations
        admin = TracLegosAdmin(dirname)

        # remove the default items
        admin.delete_all()

        # get the default wiki pages
        # TODO: add options for importing existing wiki pages
        admin.load_pages()

        # TODO:  addition of groups, milestones, versions, etc
        # via trac-admin


### site configuration

sections = set(('site-configuration', 'variables', ))

def site_configuration(*ini_files):
    """returns a dictionary of configuration from .ini files"""
    conf = ConfigMunger(*ini_files).dict()
    for section in sections:
        if section not in conf:
            conf[section] = {}
    return conf

def traclegos_argspec(*dictionaries):
    """
    returns an argspec from a list of dictionaries appropriate to 
    constructing a TracLegos instance;
    later dictionaries take precedence over earlier dictionaries
    """
    argspec = TracLegos.arguments()
    for key in argspec:
        args = [ dictionary.get(key) for dictionary in dictionaries ]
        argspec[key] = reduce(lambda x, y: y or x, args, argspec[key])
    return argspec

def traclegos_factory(ini_files, configuration, variables):
    """
    returns configuration needed to drive a TracLegos constructor
    * ini_files: site configuration .ini files    
    * configuration: dictionary of overrides to TracLegos arguments
    * variables: used for template substitution
    """
    # XXX could instead return a constructed TracLegos instance
    conf = site_configuration(*ini_files)
    argspec = traclegos_argspec(conf['site-configuration'],
                                configuration)
    argspec['vars'] = argspec['vars'] or {}
    argspec['vars'].update(conf['variables'])
    argspec['vars'].update(variables)
    return argspec

### functions for the command line front-end to TracLegos

def get_parser():
    """return an OptionParser object for TracLegos"""

    parser = OptionParser()

    # command line parser options
    parser.add_option("-c", "--conf",
                      dest="conf", action="append", default=[],
                      help="site configuration files")
    parser.add_option("-d", "--directory",
                      dest="directory", default=".",
                      help="trac projects directory")
    parser.add_option("-i", "--inherit", dest="inherit", default=None,
                      help=".ini file to inherit from")
    parser.add_option("-s", "--repository",  dest="repository",
                      help="repository type to use")
    parser.add_option("-t", dest="templates", action="append", default=[],
                      help="trac.ini templates to be applied in order")
    parser.add_option("--db", "--database",
                      dest="database", default=None,
                      help="database type to use")
    
    parser.add_option("--list-templates", dest="listprojects",
                      action="store_true", default=False,
                      help="list available TracProject PasteScript templates")
    parser.add_option("--list-repositories", dest="listrepositories",
                      action="store_true", default=False,
                      help="list repository types available for setup by TracLegos")
    parser.add_option("--list-databases", dest="listdatabases",
                      action="store_true", default=False,
                      help="list available database types available for setup by TracLegos")
    parser.add_option("--print-missing", dest="printmissing",
                      action="store_true", default=False,
                      help="print variable names missing for a given configuration")

# XXX as yet unused options
#    parser.add_option("--list-variables", dest="listvariables",
#                      help="list variables for a [someday: list of] templates") # TODO
#     parser.add_option("-r", "--requires", # XXX not used yet
#                       dest="requirements", action="append", default=[],
#                       help="requirements files for plugins") #

    parser.set_usage("%prog [options] project <project2> <...> var1=1 var2=2 ...")
    parser.set_description("assemble a trac project from components")
    return parser

def parse(parser, args=None):
    """return (legos, projects) or None"""

    options, args = parser.parse_args(args)

    # parse command line variables and determine list of projects
    projects = [] # projects to create
    vars = {} # defined variables
    for arg in args:
        if '=' in arg:
            variable, value = arg.split('=', 1)
            vars[variable] = value
        else:
            projects.append(arg)

    # list the packaged pastescript TracProject templates
    if options.listprojects:
        print 'Available projects:'
        for name, template in project_dict().items():
            print '%s: %s' % (name, template.summary)
        return

    # get the repository
    repository = None
    if options.repository: 
        repository = available_repositories().get(options.repository)
        if not repository:
            print 'Error: repository type "%s" not available\n' % options.repository
            options.listrepositories = True
    
    # list the available SCM repository setup agents
    if options.listrepositories:
        print 'Available repositories:'
        for name, repository in available_repositories().items():
            if name is not 'NoRepository': # no need to print this one
                print '%s: %s' % (name, repository.description)
        return

    # get the database
    if options.database:
        database = available_databases().get(options.database)
        if not database:
            print 'Error: database type "%s" not available\n' % options.database
            options.listdatabases = True
    else:
        database = None

    # list the available database setup agents
    if options.listdatabases:
        print 'Available databases:'
        for name, database in available_databases().items():
            print '%s: %s' % (name, database.description)
        return        

    if options.printmissing:
        projects = ['foo']

    # print help if no projects given
    if not projects: 
        parser.print_help()
        return

    # parse and apply site-configuration (including variables)
    argspec = traclegos_factory(options.conf, options.__dict__, vars)
    # project creator
    legos = TracLegos(**argspec)

    return legos, projects, { 'templates': options.templates, 
                              'repository': repository,
                              'database': database,
                              'return_missing': options.printmissing}

def main(args=None):
    """main command line entry point"""

    # command line parser
    parser = get_parser()    
    
    # get some legos
    parsed = parse(parser)
    if parsed == None:
        return # exit condition
    legos, projects, arguments = parsed

    # print missing options if told to do so
    if arguments['return_missing']:
        missing = legos.create_project('foo', **arguments)
        print '\n'.join(sorted(list(missing)))
        return

    # create the projects
    for project in projects:
        legos.create_project(project, **arguments)

if __name__ == '__main__':
    main(sys.argv[1:])
