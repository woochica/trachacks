"""
RepositoryHookAdmin:
admin panel interface for controlling hook setup and listeners
"""

from repository_hook_system.interface import IRepositoryHookSystem
from repository_hook_system.interface import IRepositoryHookSubscriber
from trac.admin.api import IAdminPanelProvider
from trac.config import Option
from trac.core import *
from trac.web.chrome import ITemplateProvider

class RepositoryHookAdmin(Component):
    """webadmin panel for hook configuration"""
    
    implements(ITemplateProvider, IAdminPanelProvider)
    listeners = ExtensionPoint(IRepositoryHookSubscriber)

    systems = ExtensionPoint(IRepositoryHookSystem) 
    # XXX maybe should be IRepositoryHookSetup?
    # or perhaps thes IRepositoryHookSetup and IRepositoryChangeListener
    # interfaces should be combined

    def system(self):
        """returns the IRepositoryHookSystem appropriate to the repository"""
        # XXX could abstract this, as this is not specific to TTW functionality
        for system in self.systems:
            if self.env.config.get('trac', 'repository_type') in system.type():
                return system            


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### methods for IAdminPanelProvider

    """Extension point interface for adding panels to the web-based
    administration interface.
    """

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if req.perm.has_permission('TRAC_ADMIN'): # XXX needed?
            system = self.system()
            if system is not None:
                for hook in system.available_hooks():
                    yield ('repository_hooks', 'Repository Hooks', hook, hook)

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        hookname = page
        system = self.system()
        data = {}
        data['hook'] = hookname

        if req.method == 'POST':

            # implementation-specific post-processing
            # XXX should probably handle errors, etc
            system.process_post(hookname, req)

            # toggle invocation of the hook
            if req.args.get('enable'):
                system.enable(hookname)
            else:
                system.disable(hookname)

            # set available listeners on a hook
            listeners = req.args.get('listeners', [])
            if isinstance(listeners, basestring):
                listeners = [ listeners ] # XXX ', '.join ?
            self.env.config.set('repository-hooks', hookname, 
                                ', '.join(listeners))

            # process posted options to configuration
            for listener in self.listeners:
                name = listener.__class__.__name__
                options = self.options(listener)
                args = dict([(key.split('%s-' % name, 1)[1], value) 
                             for key, value in req.args.items()
                             if key.startswith('%s-' % name)])
                for option in options:
                    option_type = options[option]['type']
                    section = options[option]['section']
                    value = args.get(option, '')
                    if option_type == 'bool':
                        value = value == "on" and "true" or "false"
                    self.env.config.set(section, option, value)

            self.env.config.save()
            

        data['enabled'] = system.is_enabled(hookname)
        data['can_enable'] = system.can_enable(hookname)
        activated = [ i.__class__.__name__ for i in system.subscribers(hookname) ]
        data['snippet'] = system.render(hookname, req)

        data['listeners'] = []
        for listener in self.listeners:
            _cls = listener.__class__
            data['listeners'].append(dict(name=_cls.__name__, 
                                          activated=(_cls.__name__ in activated),
                                          description=listener.__doc__,
                                          options=self.options(listener)))

        return ('repositoryhooks.html', data)

    def options(self, listener):
        _cls = listener.__class__
        options = [ (i, getattr(_cls, i)) for i in dir(_cls) 
                    if isinstance(getattr(_cls, i), Option) ]
        options = dict([(option.name, dict(section=option.section,
                                         type=option.__class__.__name__.lower()[:-6] or 'text',
                                         value=getattr(listener, attr),
                                         description=option.__doc__))
                        for attr, option in options ])
        return options
