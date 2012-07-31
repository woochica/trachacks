# -*- coding: utf-8 -*-

import inspect

from trac.core import Component, implements, TracError
from trac.admin.api import IAdminPanelProvider
from trac.config import Option, ListOption
from trac.util import Markup
from trac.util.compat import set, sorted
from trac.util.text import to_unicode
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import wiki_to_html


class IniAdminPlugin(Component):

    implements(ITemplateProvider, IAdminPanelProvider)

    excludes = ListOption('iniadmin', 'excludes',
                          'iniadmin:excludes,iniadmin:passwords',
        doc="""Excludes this options.
        Comma separated list as `section:name`.
        """)

    passwords = ListOption('iniadmin', 'passwords',
                           'trac:database,notification:smtp_password',
        doc="""Show input-type as password instead of text.
        Comma separated list as `section:name`.
        """)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            for section in sorted(set([s for s, _ in Option.registry])):
                yield ('tracini', 'trac.ini', section, section)

    def render_admin_panel(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        if page not in set([s for s, _ in Option.registry]):
            raise TracError("Invalid section %s" % page)

        _exc = [name for section, name in
                [opt.split(':') for opt in self.excludes]
                if section == page]
        _pwd = [name for section, name in
                [opt.split(':') for opt in self.passwords]
                if section == page]

        # Apply changes
        if req.method == 'POST':
            options = [option.name for (section, _), option in
                       Option.registry.iteritems() if section == page and
                       option.name not in _exc]
            modified = False
            for option, value in req.args.iteritems():
                if option in options:
                    if self.config.get(page, option) != value:
                        self.config.set(page, option, value)
                        modified = True
            if modified:
                self.log.debug("Updating trac.ini")
                self.config.save()
            req.redirect(req.href.admin(cat, page))


        add_stylesheet(req, 'iniadmin/css/iniadmin.css')

        options = sorted([option for (section, _), option in
                          Option.registry.iteritems() if section == page and
                          option.name not in _exc],
                         key=lambda a: a.name)

        options_data = []
        for option in options:
            doc = wiki_to_html(to_unicode(inspect.getdoc(option)),
                               self.env, req)
            value = self.config.get(page, option.name)
            # We assume the classes all end in "Option"
            type = option.__class__.__name__.lower()[:-6] or 'text'
            if type == 'list' and not isinstance(value,basestring):
                value = unicode(option.sep).join(list(value))
            option_data  = {'name': option.name, 'default': option.default,
                            'doc': Markup(doc), 'value': value, 'type': type}
            if type == 'extension':
                option_data['options'] = sorted(
                    impl.__class__.__name__
                    for impl in option.xtnpt.extensions(self))
            elif type == 'text' and option.name in _pwd:
                option_data['type'] = 'password'
            options_data.append(option_data)

        data = {'iniadmin': {'section': page, 'options': options_data}}
        return 'iniadmin.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('iniadmin', resource_filename(__name__, 'htdocs'))]
