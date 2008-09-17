#!/usr/bin/env python
"""
driver to create trac projects --
the head of the octopus
"""

import os
import pkg_resources
import sys

from optparse import OptionParser
from paste.script.templates import var
from paste.script.templates import Template
from trac.admin.console import TracAdmin
from trac.env import Environment
from traclegos.admin import TracLegosAdmin
from traclegos.config import ConfigMunger
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
        * site_ini: global site configuration used for all projects
        * vars: variables for interpolation of trac.ini
        * inherit: inherited configuration to update
        """

        self.directory = directory
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

    def project_templates(self, templates):
        # apply site configuration last (override)
        return ProjectTemplates(*(templates + self.site_templates))
    # TODO: add the self.options to the templates

    # arguments to RepositorySetup.setup that may be interpolated from variables
    def repository_fields(self, project):
        return { 'SVNSync': {'repository_dir': os.path.join(self.directory, project, 'mirror') },
                 'NewSVN': {'repository_dir': os.path.join(self.directory, project, 'svn') }
                 }

    def create_project(self, project, templates, vars=None,
                       repository=None):
        """
        * project: directory name of project
        * templates to be applied
        * vars: variables for interpolation
        """
        # TODO: db stuff; 
        
        ### set variables

        dirname = os.path.join(self.directory, project)
        _vars = vars or {}
        vars = self.vars.copy()
        vars.update(_vars)
        vars['project'] = project        

        ### munge configuration

        # get templates
        if not isinstance(templates, ProjectTemplates):
            if repository:
                templates.append(repository.config())
            templates = self.project_templates(templates)

        # determine the vars
        optdict = templates.vars(self.options)
        repo_fields = {}
        if repository:
            vars2dict(optdict, *repository.options)
            repo_fields = self.repository_fields(project).get(repository.name, {})

        ### interpolate configuration

        command = create_distro_command(interactive=self.interactive)
        
        # check for missing variables
        missing = templates.missing(vars)
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
        
        
        # create the trac environment
        options = templates.options_tuples(vars)
        options.append(('project', 'name', project)) # XXX needed?
        if self.inherit:
            options.append(('inherit', 'file', self.inherit))
        env = Environment(dirname, create=True, options=options)

        ### repository setup
        if repository:
            repository.setup(**vars)
            repos = env.get_repository()
            repos.sync()

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
        print >> fp, _conf
        fp.close()

        # TODO: update the inherited file:
        # * intertrac

        ### trac-admin operations
        admin = TracLegosAdmin(dirname)

        # remove the default items
        admin.delete_all()

        # get the default wiki pages
        # TODO: add options for importing existing wiki pages
        cnx = env.get_db_cnx()
        cursor = cnx.cursor()
        pages_dir = pkg_resources.resource_filename('trac.wiki', 
                                                    'default-pages') 
        admin._do_wiki_load(pages_dir, cursor) # should probably make this silent
        cnx.commit()

        # TODO: trac-admin upgrade the project
        

        # TODO (wishlist):  addition of groups, milestones, versions, etc
        # via trac-admin


### functions for the command line front-end to TracLegos

def get_parser():
    """return an OptionParser object for TracLegos"""

    parser = OptionParser()
    # XXX this could (should?) share configuration with TracLegos.options
    parser.add_option("-c", "--conf",
                      dest="conf", action="append", default=[],
                      help="site configuration files")
    parser.add_option("-d", "--directory",
                      dest="directory", default=".",
                      help="trac projects directory")
    parser.add_option("-i", "--inherit", dest="inherit", default=None,
                      help=".ini file to inherit from")
    parser.add_option("-r", "--requires", # XXX not used yet
                      dest="requirements", action="append", default=[],
                      help="requirements files for plugins") #
    parser.add_option("-s", "--repository",  dest="repository",
                      help="repository type to use")
    parser.add_option("-t", dest="templates", action="append", default=[],
                      help="trac.ini templates to be applied in order")
    
    parser.add_option("--list-templates", dest="listprojects",
                      action="store_true", default=False,
                      help="list available TracProject PasteScript templates")
#    parser.add_option("--list-variables", dest="listvariables",
#                      help="list variables for a [someday: list of] templates") # TODO
    parser.add_option("--list-repositories", dest="listrepositories",
                      action="store_true", default=False,
                      help="list repositories available for setup by TracLegos")

    parser.set_usage("%prog [options] project <project2> <...> var1=1 var2=2 ...")
    parser.set_description("assemble a trac project from components")
    return parser

def parse(parser, args=None):
    """return (legos, projects) or None"""

    options, args = parser.parse_args(args)

    vars = {} # defined variables

    # parse and apply site-configuration (including variables)
    conf = ConfigMunger(*options.conf)
    if 'variables' in conf.sections():
        vars.update(conf['variables'])
    # TODO: set options from configuration

    # parse command line variables and determine list of projects
    projects = []
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

    repository = None
    if options.repository: # get the repository
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

    if not projects: # print help if no projects given
        parser.print_help()
        return

    # project creator
    legos = TracLegos(directory=options.directory, inherit=options.inherit, vars=vars)
    
    # XXX this is hackish
    # should return:
    # { project: { 'repository': repository, 'templates': options.templates, }
    # for each project
    return legos, projects, options.templates, repository

def main(args=None):
    """main command line entry point"""

    # command line parser
    parser = get_parser()    
    
    # get some legos
    try:
        legos, projects, templates, repository = parse(parser)
    except TypeError:
        return # XXX potentially fail silently 

    # create the projects
    for project in projects:
        legos.create_project(project, templates, repository=repository)

if __name__ == '__main__':
    main(sys.argv[1:])
