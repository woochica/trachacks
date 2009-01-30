"""
TTW view for project creation and serving trac
"""

import cgi
import os
import string
import sys
import tempfile

from genshi.core import Markup
from genshi.template import TemplateLoader
from trac.web.main import dispatch_request
from traclegos.config import ConfigMunger
from traclegos.db import available_databases
from traclegos.legos import site_configuration
from traclegos.legos import traclegos_factory
from traclegos.legos import TracLegos
from traclegos.pastescript.string import PasteScriptStringTemplate
from traclegos.pastescript.var import vars2dict, dict2vars
from traclegos.project import project_dict
from traclegos.repository import available_repositories
from webob import Request, Response, exc

# TODO: better handling of errors (not very friendly, currently)

template_directory = os.path.join(os.path.dirname(__file__), 'templates')

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

        # trac projects available
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

        # available SCM repository types
        self.repositories = available_repositories()
        self.available_repositories = kw.get('available_repositories')
        if self.available_repositories is None:
            self.available_repositories = ['NoRepository'] + [ name for name in self.repositories.keys() if name is not 'NoRepository' ]
            
        else:
            for name in self.repositories.keys():
                if name not in self.available_repositories:
                    del self.repositories[name]

        # available database types
        self.databases = available_databases()
        self.available_databases = kw.get('available_databases')
        if self.available_databases is None:
            self.available_databases = [ 'SQLite' ] + [ name for name in self.databases.keys() if name is not 'SQLite' ]
        else:
            for name in self.databases.keys():
                if name not in self.available_databases:
                    del self.databases[name]
                    
        # TODO: pop project-details if this is an empty step

    ### methods dealing with HTTP
    def __call__(self, environ, start_response):

        req = Request(environ) 
        
        step = req.path_info.strip('/')
        if step in self.steps:
            method = ''.join(index and token.title() or token 
                             for index, token in enumerate(step.split('-')))

            # if POST-ing, validate the request and store needed information
            errors = None
            if req.method == 'POST':

                project = req.POST.get('project')
                if not project and step != 'create-project':
                    res = exc.HTTPSeeOther("No session found", location="create-project")
                    return res(environ, start_response)
        
                validator = getattr(self, 'validate' + method[0].upper() + method[1:])
                errors = validator(req)
                if not errors: # success
                    index = self.steps.index(step)
                    if index == len(self.steps) - 1:
                        destination = self.done % self.projects[project]['vars']
                        self.projects.pop(project) # successful project creation
                    else:
                        destination = '%s?project=%s' % (self.steps[index + 1], project)
                    res = exc.HTTPSeeOther(destination, location=destination)
                    return res(environ, start_response)
            else:
                if step != 'create-project':
                    project = req.GET.get('project')
                    if project in self.projects:
                        # TODO: put this and the project data into data
                        pass
                    else:
                        res = exc.HTTPSeeOther("No session found", location="create-project")
                        return res(environ, start_response)
                        
            
            data = getattr(self, method)(req, errors)
            data['errors'] = errors
            template = self.loader.load("%s.html" % step)
            html =  template.generate(**data).render('html', doctype='html')
            res = self.get_response(html)
            return res(environ, start_response)

        environ['trac.env_parent_dir'] = self.directory

        # could otherwise take over the index.html serving ourselves
        environ['trac.env_index_template'] = os.path.join(template_directory, 'index.html')
        
        return dispatch_request(environ, start_response) 
        
    def get_response(self, text, content_type='text/html'):
        """returns a response object for HTML/text input"""
        res = Response(content_type=content_type, body=text)
        res.content_length = len(res.body)
        return res

    ### methods for URIs
    def createProject(self, req, errors=None):
        """first project creation step:  initial project data"""
        data = {}
        data['URL'] = req.url.rsplit('create-project', 1)[0]
        data['projects'] = self.available_templates
        data['next'] = 'Project Details'
        return data

    def validateCreateProject(self, req):

        # check for errors
        errors = []        
        project = req.POST.get('project')
        if project:
            if project in self.projects: # TODO check for existing trac projects
                errors.append("The project '%s' already exists" % project)
            else:
                self.projects[project] = {} # new project
        else:
            errors.append('No project URL specified')


        project_type = req.POST.get('project_type')
        assert project_type in self.available_templates

        # get the project logo
        logo = req.POST['logo']
        logo_file = None
        if logo:
            if not logo.startswith('http://') or logo.startswith('https://'):
                if os.path.exists(logo):
                    logo_file = file(logo, 'rb')
                    logo_file_name = os.path.basename(logo)
                else:
                    errors.append("Logo file not found: %s" % logo)

        if errors:
            return errors

        ### process the request and save necessary data

        project_data = self.projects[project]
        project_data['type'] = project_type
        project_data['vars'] = self.legos.vars.copy()
        project_data['vars'].update({'project': project,
                                     'description': req.POST.get('project_name').strip() or project,
                                     'url': req.POST.get('alternate_url')
                                     })

        project_data['config'] = {}
        project_data['config']['header_logo'] = {'link': req.POST['alternate_url'] }

        # get an uploaded logo
        # note that uploaded logos will override logo files/links 
        # (should this be an error instead?)
        uploaded_logo = req.POST['logo_file']
        if isinstance(uploaded_logo, cgi.FieldStorage):
            logo_file_name = uploaded_logo.filename
            logo_file = uploaded_logo.file

        project_data['logo_file'] = logo_file
        if logo_file:
            logo = 'site/%s' % logo_file_name

        project_data['config']['header_logo']['src'] = logo
        project_data['vars']['logo'] = logo
        
        # TODO:  get the favicon from the alternate URL or create one from the logo

        # get a list of TRAC_ADMINs
        # XXX this is a hack, for now
        project_data['admins'] = req.POST['trac_admins'].replace(',', ' ').split()

    def projectDetails(self, req, errors=None):
        """second project creation step: project details
        svn repo, mailing lists (TODO)
        """
        project = req.GET['project']
        data = {'project': project,
                'repositories': [ self.repositories[name] for name in self.available_repositories ],
                'excluded_fields': dict((key, value.keys()) for key, value in self.legos.repository_fields(project).items()),
                'databases': [ self.databases[name] for name in self.available_databases ] } 

        # get the database strings
        data['db_string'] = {}
        for database in data['databases']:
            dbstring = database.db_string()
            dbstring = string.Template(dbstring).safe_substitute(**self.projects[project]['vars'])
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

    def validateProjectDetails(self, req):

        # check for errors
        errors = []
        project = req.POST.get('project')
        project_data = self.projects.get(project)
        if project_data is None:
            errors.append('Project not found')

        # repository information
        project_data['repository'] = None
        repository = req.POST.get('repository')
        if repository in self.available_repositories:
            args = dict((arg.split('%s_' % repository, 1)[1], value) 
                        for arg, value in req.POST.items()
                        if arg.startswith('%s_' % repository))
            project_data['repository'] = self.repositories[repository]
            project_data['vars'].update(args)
            project_data['vars'].update(self.legos.repository_fields(project).get(repository, {}))

        # database information
        project_data['database'] = None
        database = req.POST.get('database')
        if database in self.available_databases:
            project_data['database'] = self.databases[database]

        return errors

    def projectVariables(self, req, errors=None):
        """final project creation step:  filling in the project variables"""
        
        project = req.GET.get('project')
        project_data = self.projects[project]
        templates = [project_data['type'], project_data['config']]
        repository = project_data['repository']
        if repository:
            templates.append(repository.config())
        templates = self.legos.project_templates(templates)
        options = templates.options()
        for var in project_data['vars']:
            options.pop(var, None)
        project_data['templates'] = templates
        data = {'project': project,
                'options': options.values()}
        
        return data

    def validateProjectVariables(self, req):
        errors = []

        # XXX to deprecate ?
        project = req.POST.get('project')
        if project not in self.projects:
            errors.append('Project not found')

        if errors:
            return errors

        project_data = self.projects[project]
        project_data['vars'].update(req.POST)

        # create the project
        self.legos.create_project(project, 
                                  project_data['templates'], 
                                  project_data['vars'], 
                                  repository=project_data['repository'])

        project_dir = os.path.join(self.directory, project)

        # write the logo_file to its new location
        logo_file = project_data['logo_file']
        if logo_file:
            logo_file_name = os.path.basename(project_data['vars']['logo'])
            filename = os.path.join(project_dir, 'htdocs', logo_file_name)
            logo = file(filename, 'wb')
            logo.write(logo_file.read())
            logo.close()
            
        # TODO: favicons from logo or alternate url

        # TODO: add authenticated user to TRAC_ADMIN of the new site
        # (and redirect to the admin panel?)
        # XXX hack for now
        for admin in project_data['admins']:
            import subprocess
            subprocess.call(['trac-admin', project_dir, 'permission', 'add', admin, 'TRAC_ADMIN'])

        
