# -*- coding: utf-8 -*-

import inspect
import re

from trac.core import Component, implements, TracError
from trac.admin.api import IAdminPanelProvider
from trac.config import Option, ListOption
from trac.util import Markup
from trac.util.compat import set, sorted, any
from trac.util.text import to_unicode
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import wiki_to_html


class IniAdminPlugin(Component):

    implements(ITemplateProvider, IAdminPanelProvider)

    excludes = ListOption('iniadmin', 'excludes', 'iniadmin:*',
        doc="""Excludes this options.
        Comma separated list as `section:name` with wildcard characters
        (`*`, `?`).
        """)

    passwords = ListOption('iniadmin', 'passwords',
                           'trac:database,notification:smtp_password',
        doc="""Show input-type as password instead of text.
        Comma separated list as `section:name` with wildcard characters.
        """)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            excludes_match = self._patterns_match(self.excludes)
            for section in sorted(self._get_sections_set(excludes_match)):
                yield ('tracini', 'trac.ini', section, section)

    def render_admin_panel(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')

        excludes_match = self._patterns_match(self.excludes)
        if page not in self._get_sections_set(excludes_match):
            raise TracError("Invalid section %s" % page)

        options = sorted(
            [option for (section, name), option
                    in Option.registry.iteritems()
                    if section == page and \
                       not excludes_match('%s:%s' % (section, name))],
            key=lambda opt: opt.name)

        # Apply changes
        if req.method == 'POST':
            modified = False
            for name, value in req.args.iteritems():
                if any(name == opt.name for opt in options):
                    if self.config.get(page, name) != value:
                        self.config.set(page, name, value)
                        modified = True
            if modified:
                self.log.debug("Updating trac.ini")
                self.config.save()
            req.redirect(req.href.admin(cat, page))

        add_stylesheet(req, 'iniadmin/css/iniadmin.css')

        password_match = self._patterns_match(self.passwords)
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
            elif type == 'text' and \
                 password_match('%s:%s' % (option.section, option.name)):
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

    def _get_sections_set(self, excludes_match):
        return set([section
                    for section, name in Option.registry
                    if not excludes_match('%s:%s' % (section, name))])

    def _patterns_match(self, patterns):
        if not patterns:
            return lambda val: False

        wildcard_re = re.compile('([*?]+)|([^*?A-Za-z0-9_]+)')
        def replace(match):
            group = match.group
            if group(1) == '?':
                return '[^:]'
            if group(1) == '*':
                return '[^:]*'
            return re.escape(group(2))

        patterns_re = r'\A(?:%s)\Z' % \
                      '|'.join([wildcard_re.sub(replace, pattern)
                               for pattern in patterns])
        return re.compile(patterns_re).match
