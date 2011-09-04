# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Itamar Ostricher <itamarost@gmail.com>
# Copyright (C) 2011 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.util.compat import sorted
from trac.web.chrome import Chrome
from tractags.api import TagSystem, _


class TagChangeAdminPanel(Component):

    implements(IAdminPanelProvider)

    # AdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TAGS_ADMIN' in req.perm:
            yield ('tags', _('Tag System'), 'replace', _('Replace'))

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TAGS_ADMIN')
        data = {}
        tag_system = TagSystem(self.env)
        if req.method == 'POST':
            # Replace Tag
            allow_delete = req.args.get('allow_delete')
            new_tag = req.args.get('tag_new_name').strip()
            new_tag =  not new_tag == u'' and new_tag or None
            if not (allow_delete or new_tag):
                data['error'] = _("""Selected current tag(s) and either
                                  new tag or delete approval are required""")
            else:
                comment = req.args.get('comment', u'')
                old_tags = req.args.get('tag_name')
                if old_tags:
                    # Provide list regardless of single or multiple selection.
                    old_tags = isinstance(old_tags, list) and old_tags or \
                               [old_tags]
                    tag_system.replace_tag(req, old_tags, new_tag, comment,
                                           allow_delete)
                data['selected'] = new_tag

        all_tags = sorted(tag_system.get_all_tags(req, '-dummy'))
        data['tags'] = all_tags
        try:
            Chrome(self.env).add_textarea_grips(req)
        except AttributeError:
            # Element modifiers unavailable before Trac 0.12, skip gracefully.
            pass
        return 'admin_tag_change.html', data

