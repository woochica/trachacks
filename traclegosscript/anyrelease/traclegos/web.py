"""
TTW view for project creation and serving trac
"""

import cgi
import os
import string
import subprocess
import sys
import time

from genshi.core import Markup
from genshi.template import TemplateLoader
from martini.config import ConfigMunger
from trac.env import open_environment
from trac.web.main import dispatch_request
from trac.web.main import RequestDispatcher
from traclegos.db import available_databases
from traclegos.legos import traclegos_factory
from traclegos.legos import TracLegos
from traclegos.pastescript.string import PasteScriptStringTemplate
from traclegos.pastescript.var import vars2dict, dict2vars
from traclegos.project import project_dict
from traclegos.repository import available_repositories
from webob import Request, Response, exc

# TODO: better handling of errors (not very friendly, currently)

template_directory = os.path.join(os.path.dirname(__file__), 'templates')

### project creation steps

class Step(object):
    """base class for TTW project creation steps"""

    def __init__(self, view):
        self.view = view
        self.template = self.name + '.html'

class CreateProject(Step):
    """project creation step + transition"""
    name = 'create-project'
    def data(self, project):
        """data needed for template rendering"""
        return { 'URL': project['base_url'],
                 'projects': self.view.available_templates }

    def display(self, project):
        """whether to display this step"""
        return True

    def errors(self, project, input):
        """check for errors"""
        errors = []        
        project_name = input.get('project')
        if project_name:            
            projects = self.view.projects.keys() + os.listdir(self.view.directory)
            if project_name in projects:
                errors.append("The project '%s' already exists" % project_name)
        else:
            errors.append('No project URL specified')


        project_type = input.get('project_type')
        assert project_type in self.view.available_templates

        # get the project logo
        logo = input['logo']
        if logo:
            if not logo.startswith('http://') or logo.startswith('https://'):
                if not os.path.exists(logo):
                    errors.append("Logo file not found: %s" % logo)
        return errors

    def transition(self, project, input):
        """transition following this step"""
        logo = input['logo']
        logo_file = None
        if logo and not (logo.startswith('http://') or logo.startswith('https://')):
            logo_file = file(logo, 'rb')
            logo_file_name = os.path.basename(logo)

        project['type'] = input['project_type']
        project['vars'] = self.view.legos.vars.copy()
        project['vars'].update({'project': input['project'],
                                'description': input.get('project_name').strip() or input['project'],
                                'url': input.get('alternate_url')
                                })
        project['config'] = {}
        project['config']['header_logo'] = {'link': input['alternate_url'] }

        # get an uploaded logo
        # note that uploaded logos will override logo files/links 
        # (should this be an error instead?)
        uploaded_logo = input['logo_file']
        if isinstance(uploaded_logo, cgi.FieldStorage):
            logo_file_name = uploaded_logo.filename
            logo_file = uploaded_logo.file

        project['logo_file'] = logo_file
        if logo_file:
            logo = 'site/%s' % logo_file_name

        project['config']['header_logo']['src'] = logo
        project['vars']['logo'] = logo
        
        # TODO:  get the favicon from the alternate URL or create one from the logo

        # get a list of TRAC_ADMINs
        # XXX this is a hack, for now
        project['admins'] = input['trac_admins'].replace(',', ' ').split()
        

class ProjectDetails(Step):
    """
    second project creation step: project details
    svn repo, mailing lists (TODO)
    """
    name = 'project-details'
    def data(self, project):
        """data needed for template rendering"""
        project_name = project['vars']['project']
        data = {'project': project_name,
                'repositories': [ self.view.repositories[name] for name in self.view.available_repositories ],
                'excluded_fields': dict((key, value.keys()) for key, value in self.view.legos.repository_fields(project_name).items()),
                'databases': [ self.view.databases[name] for name in self.view.available_databases ] } 

        # get the database strings
        data['db_string'] = {}
        for database in data['databases']:
            dbstring = database.db_string()
            dbstring = string.Template(dbstring).safe_substitute(**project['vars'])
            template = PasteScriptStringTemplate(dbstring)
            missing = template.missing()
            if missing:
                vars = vars2dict(None, *database.options)
                missing = dict([(i, 
                                 '<input type="text" name="%s-%s" value="%s"/>' % (database.name, i, getattr(vars.get(i), 'default', '')))
                                for i in missing])
                dbstring = string.Template(dbstring).substitute(**missing)
                dbstring = Markup(dbstring)
            data['db_string'][database.name] = dbstring
        return data
    
    def display(self, project):
        """display this step if there is something to do"""
        project_details = [ self.view.available_repositories, self.view.available_databases ]
        return not sum([len(i) for i in project_details]) == len(project_details)
    
    def errors(self, project, input):
        # TODO
        return []
    
    def transition(self, project, input):
        """transition to the next step"""
        
        # repository information
        project['repository'] = None
        repository = input.get('repository')
        if not repository:
            # repository is specified by policy
            assert len(self.view.available_repositories) == 1
            repository = self.view.available_repositories[0]

        if repository in self.view.available_repositories: # XXX musn't this be true?!?
            args = dict((arg.split('%s_' % repository, 1)[1], value) 
                        for arg, value in input.items()
                        if arg.startswith('%s_' % repository))
            project['repository'] = self.view.repositories[repository]
            project['vars'].update(args)
            project['vars'].update(self.view.legos.repository_fields(project['vars']['project']).get(repository, {}))

        # database information
        project['database'] = None
        database = input.get('database')
        if not database:
            # database is specified by policy
            assert len(self.view.available_databases) == 1
            database = self.view.available_databases[0]
        if database in self.view.available_databases: # XXX musn't this be true?!?
            project['database'] = self.view.databases[database]

class ProjectVariables(Step):
    """final project creation step:  filling in the project variables"""
    name = 'project-variables'
    def data(self, project):
        """data needed for template rendering"""
        templates = self.templates(project)
        options = templates.options()
        for var in project['vars']:
            options.pop(var, None)
        return  {'project': project['vars']['project'],
                 'options': options.values()}
        
    def display(self, project):
        templates = self.templates(project)
        options = templates.options()
        for var in project['vars']: # could use set
            options.pop(var, None)
        return bool(options)
    
    def errors(self, project, input):
        # TODO
        return []
    
    def transition(self, project, input):
        """create the project from TTW input"""

        # add input (form) variables to the project variables
        project['vars'].update(input)

        # don't add the repository directory here so that we can 
        # sync asynchronously
        # XXX hack
        repository_dir = project['vars'].get('repository_dir')
        project['vars']['repository_dir'] = ''

        # create the project
        self.view.legos.create_project(project['vars']['project'],
                                       self.templates(project),
                                       project['vars'],
                                       database=project['database'],
                                       repository=project['repository'])

        project_dir = os.path.join(self.view.directory, project['vars']['project'])

        # write the logo_file to its new location
        logo_file = project['logo_file']
        if logo_file:
            logo_file_name = os.path.basename(project['vars']['logo'])
            filename = os.path.join(project_dir, 'htdocs', logo_file_name)
            logo = file(filename, 'wb')
            logo.write(logo_file.read())
            logo.close()
            
        # TODO: favicons from logo or alternate url

        # TODO: add authenticated user to TRAC_ADMIN of the new site
        # (and redirect to the admin panel?)
        # XXX hack for now
        for admin in project['admins']:
            subprocess.call(['trac-admin', project_dir, 'permission', 'add', admin, 'TRAC_ADMIN'])

        # XXX hack to sync the repository asynchronously
        if repository_dir:
            ini = os.path.join(project_dir, 'conf', 'trac.ini')
            conf = ConfigMunger(ini, { 'trac': {'repository_dir': repository_dir}})
            f = file(ini, 'w')
            conf.write(f)
            subprocess.Popen(['trac-admin', project_dir, 'resync'])


    def templates(self, project):
        templates = [project['type'], project['config']]
        repository = project['repository']
        if repository:
            templates.append(repository.config())
        return self.view.legos.project_templates(templates)

class View(object):
    """WebOb view which wraps trac and allows TTW project creations"""

    def __init__(self, **kw):

        # trac project creator
        argspec = traclegos_factory(kw.get('conf', ()),
                                    kw,
                                    kw.get('variables', {}))
        self.legos = TracLegos(**argspec)
        self.legos.interactive = False
        self.directory = self.legos.directory # XXX needed?
        self.available_templates = kw.get('available_templates') or project_dict().keys()
        assert self.available_templates
            
        # genshi template loader
        self.loader = TemplateLoader(template_directory, auto_reload=True)

        # storage of intermittent projects
        self.projects = {} 

        # URL to redirect to after project creation
        self.done = '/%(project)s'

        # steps of project creation
        self.steps = [ 'create-project', 'project-details', 'project-variables' ]
        self.steps = [ (step.name, step(self)) for step in [ CreateProject, ProjectDetails, ProjectVariables ] ]

        # available SCM repository types
        self.repositories = available_repositories()
        self.available_repositories = kw.get('available_repositories')
        if self.available_repositories is None:
            self.available_repositories = ['NoRepository'] + [ name for name in self.repositories.keys() if name is not 'NoRepository' ]
            
        else:
            for name in self.repositories.keys():
                if name not in self.available_repositories:
                    del self.repositories[name]
        if 'variables' in kw:
            # set repository options defaults from input variables
            for repository in self.repositories.values():            
                for option in repository.options:
                    option.default = kw['variables'].get(option.name, option.default)

        # available database types
        self.databases = available_databases()
        self.available_databases = kw.get('available_databases')
        if self.available_databases is None:
            self.available_databases = [ 'SQLite' ] + [ name for name in self.databases.keys() if name is not 'SQLite' ]
        else:
            for name in self.databases.keys():
                if name not in self.available_databases:
                    del self.databases[name]

    def trac_projects(self):
        """returns existing Trac projects"""
        proj = {}
        for i in os.listdir(self.directory):
            try:
                env = open_environment(os.path.join(self.directory, i))
            except:
                continue
            proj[i] = env
        return proj
                    
    ### methods dealing with HTTP
    def __call__(self, environ, start_response):

        req = Request(environ)                                     
        step = req.path_info.strip('/')

        if step in [i[0] for i in self.steps]:
            # determine which step we are on
            index = [i[0] for i in self.steps].index(step)
        else:
            # delegate to Trac
            # could otherwise take over the index.html serving ourselves
            environ['trac.env_parent_dir'] = self.directory
            environ['trac.env_index_template'] = os.path.join(template_directory, 'index.html')
            res = dispatch_request(environ, start_response)
            return res
            
        # if POST-ing, validate the request and store needed information
        errors = None
        name, step = self.steps[index]
        base_url = req.url.rsplit(step.name, 1)[0]
        project = req.params.get('project')
        if req.method == 'POST':

            # check for project existence
            if not project and index:
                res = exc.HTTPSeeOther("No session found", location="create-project")
                return res(environ, start_response)
            if index:
                if project not in self.projects:
                    errors.append('Project not found')

            project_data = self.projects.get(project)
            errors = step.errors(project_data, req.POST)
            if not index:
                project_data = self.projects[project] = {}

            # set *after* error check so that `create-project` doesn't find itself
            project_data['base_url'] = base_url 
            
            if not errors: # success
                step.transition(project_data, req.POST)

                # find the next step and redirect to it
                while True:
                    index += 1
                    
                    if index == len(self.steps):
                        destination = self.done % self.projects[project]['vars']
                        time.sleep(1) # XXX needed?
                        self.projects.pop(project) # successful project creation
                        break
                    else:
                        name, step = self.steps[index]
                        if step.display(project_data):
                            destination = '%s?project=%s' % (self.steps[index][0], project)        
                            break
                        else:
                            step.transition(project_data, {})
                res = exc.HTTPSeeOther(destination, location=destination)
                return res(environ, start_response)
        else: # GET
            project_data = self.projects.get(project, {})
            project_data['base_url'] = base_url
            if index:
                if project not in self.projects:
                    res = exc.HTTPSeeOther("No session found", location="create-project")
                    return res(environ, start_response)
            while not step.display(project_data):
                break
                step.transition(project_data, {})
                

        data = step.data(project_data)
        data['errors'] = errors
        template = self.loader.load(step.template)
        html =  template.generate(**data).render('html', doctype='html')
        res = self.get_response(html)
        return res(environ, start_response)
        
    def get_response(self, text, content_type='text/html'):
        """returns a response object for HTML/text input"""
        res = Response(content_type=content_type, body=text)
        res.content_length = len(res.body)
        return res
