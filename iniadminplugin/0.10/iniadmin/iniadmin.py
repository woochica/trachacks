from trac.core import *
from trac.wiki.formatter import wiki_to_html
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.util import escape, Markup, sorted
from webadmin.web_ui import IAdminPageProvider
import inspect
from trac.config import Option, BoolOption, IntOption, ListOption, \
                        ExtensionOption
try:
    set = set
except:
    from sets import Set as set

class IniAdminPlugin(Component):
    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            for section in sorted(set([s for s, _ in Option.registry])):
                yield ('tracini', 'trac.ini', section, section)

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        if page not in set([s for s, _ in Option.registry]):
            raise TracError("Invalid section %s" % page)

        # Apply changes
        if req.method == 'POST':
            options = [option.name for (section, _), option in
                       Option.registry.iteritems() if section == page]
            modified = False
            for option, value in req.args.iteritems():
                if option in options:
                    if self.env.config.get(page, option) != value:
                        self.env.config.set(page, option, value)
                        modified = True
            if modified:
                self.env.log.debug("Updating trac.ini")
                self.env.config.save()
            req.redirect(self.env.href.admin(cat, page))

            
        add_stylesheet(req, 'iniadmin/css/iniadmin.css')

        options = sorted([option for (section, _), option in
                          Option.registry.iteritems() if section == page],
                         key=lambda a: a.name)

        hdf_options = []
        for option in options:
            doc = wiki_to_html(inspect.getdoc(option), self.env, req)
            value = self.env.config.get(page, option.name)
            # We assume the classes all end in "Option"
            type = option.__class__.__name__.lower()[:-6] or 'text'
            hdf_option  = {'name': option.name, 'default': option.default,
                           'doc': Markup(doc), 'value': value, 'type': type}
            if type == 'extension':
                options = []
                for impl in option.xtnpt.extensions(self):
                    options.append(impl.__class__.__name__)
                options.sort()
                hdf_option['options'] = options
            hdf_options.append(hdf_option)

        req.hdf['iniadmin.section'] = page
        req.hdf['iniadmin.options'] = hdf_options
        return 'iniadmin.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('iniadmin', resource_filename(__name__, 'htdocs'))]
