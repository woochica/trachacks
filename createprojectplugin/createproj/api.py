import os
import ConfigParser
from string import Template

from trac.core import *
from trac.env import Environment
from trac.config import Option, ListOption
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor

from webadmin.web_ui import IAdminPageProvider


__all__ = ['CreateProjectPlugin']


class CreateProjectPlugin(Component):

    files_to_delete = ListOption('customsetup', 'files_to_delete',
        doc="""A comma separated list of files to delete after a project has
        been created.   The paths should be relative to the project environment
        directory.""")

    project_defaults_ini = Option('customsetup', 'project_defaults_ini',
        doc="""(Optional) The path to an ini file that contains the default 
        settings for new projects.""")

    implements(ITemplateProvider, IAdminPageProvider, IPermissionRequestor)


    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'PROJECT_CREATE'


    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('PROJECT_CREATE'):
            yield ('general', 'General', 'createproj', 'Create New Project')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('PROJECT_CREATE')
        if page != 'createproj':
            raise TracError("Invalid page %s" % page)

        # filter out the project-specific arguments and remove the prefix
        prefix = 'createproject.'
        projkeys = filter(lambda x: x.startswith(prefix), req.args.iterkeys())
        args = dict((key[len(prefix):], req.args[key]) for key in projkeys)

        if req.method == 'POST':
            # handle form submission
            (projects_root_url, _) = os.path.split(self.env.project_url)
            (projects_root_path, _) = os.path.split(self.env.path)

            project_url = os.path.join(projects_root_url, args['dir_name'])
            path = os.path.join(projects_root_path, args['dir_name'])

            args.setdefault('url', project_url)
            args.setdefault('path', path)

            new_env = self._do_create_proj(args)
            self._add_global_settings(new_env, args)
            self._delete_unwanted_files(new_env)
            req.redirect(project_url)

        args.setdefault('repos_type', 'svn')

        # store the input arguments back in the form fields so the user
        # can correct errors
        for name, val in args.iteritems():
            req.hdf[prefix + name] = val

        add_stylesheet(req, 'createproj/css/createproj.css')
        return 'createproj.cs', None


    def _do_create_proj(self, args):
        self.log.debug('Preparing initial project environment settings.')
        default_options = [
            ('header_logo', 'link', args['url']),
            ('project', 'name', args['full_name']),
            ('project', 'descr', args['desc']),
            ('project', 'url', args['url']),
            ('trac', 'repository_dir', args['repos_path']),
            ('trac', 'repository_type', args['repos_type'])
        ]
        custom_options = _read_options(self.project_defaults_ini, args)

        # combine the input settings, with the ini-file options overriding the
        # defaults
        proj_options = custom_options + \
            filter(lambda x: x[:2] not in custom_options, default_options)

        self.log.debug('Creating environment.')
        new_env = Environment(args['path'], True, proj_options)
        return new_env

    def _add_global_settings(self, new_env, args):
        self.log.debug('Adding project-specific settings to global trac.ini file.')
        custom_shared_options = [
            ('intertrac', args['intertrac_name'] + '.title', args['full_name']),
            ('intertrac', args['intertrac_name'] + '.url', args['url']),
            ('intertrac', args['intertrac_name'] + '.compat', 'false')
        ]
        _set_shared_site_options(new_env, custom_shared_options)

    def _delete_unwanted_files(self, new_env):
        self.log.debug('Deleting unwanted files from new environment.')
        for afile in self.files_to_delete:
            fullpath = os.path.join(new_env.path, afile)
            self.log.debug('Deleting file: ' + fullpath)
            os.remove(fullpath)


    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('createproj', resource_filename(__name__, 'htdocs'))]


def _read_options(filepath, keyword_substitutions):
    config = ConfigParser.ConfigParser()
    config.read(filepath)

    raw_options = []
    for section in config.sections():
        for option, value in config.items(section, True):
            raw_options += [(section, option, value)]

    custom_options = [tuple([Template(elem).safe_substitute(keyword_substitutions) \
        for elem in option]) for option in raw_options]

    return custom_options


def _set_shared_site_options(env, options):
    shared_cfg = env.config.site_parser

    for section, option, value in options:
        if not shared_cfg.has_section(section):
            shared_cfg.add_section(section)
        shared_cfg.set(section, option, value)

    fp = open(env.config.site_filename, 'w')
    shared_cfg.write(fp)
    fp.close()

