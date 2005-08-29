from trac.core import *
from trac.util import TracError
from trac.web.chrome import add_stylesheet, ITemplateProvider, add_stylesheet
from trac.web.href import Href
from webadmin.web_ui import IAdminPageProvider
from model import LinkInfo
from GeneralLinkSyntax import GeneralLinkSyntaxProvider
import os

class LinkAdmin(Component):
    implements(IAdminPageProvider, ITemplateProvider)

    # IAdminPageProvider methods

    # required permission to access this page
    _perm = 'TRAC_ADMIN'

    def get_admin_pages(self, req):
        # FIXME: more suitable permission should be used
        if req.perm.has_permission(self._perm):
            # (category, category_label, page, page_label)
            yield ('general', 'General', 'link', 'Links')

    def _set_message(self, req, cls, text):
        req.session['message_text'] = text
        req.session['message_class'] = cls

    def _get_message(self, req):
        return req.session.get('message_text', ''), \
               req.session.get('message_class', 'none')

    def _clear_message(self, req):
        dic = req.session
        if dic.has_key('message_text'):
            dic.pop('message_text')
        if dic.has_key('message_class'):
            dic.pop('message_class')

    def _notify(self, req, text):
        self._set_message(req, 'notify', text)

    def _error(self, req, text):
        self._set_message(req, 'error', 'ERROR: ' + text)

    
    def process_admin_request(self, req, category, page, name):
        req.perm.assert_permission(self._perm)

        # this page may called like
        # /proj/admin/general
        # /proj/admin/general/link
        # /proj/admin/general/link/name
        base_href = self.env.href.admin('general', 'link')

        # post back actions:
        #   add ... add and redirect to top
        #   modify ... modify and redirect self or renamed self
        #   remove ... redirect to top
        
        prov = GeneralLinkSyntaxProvider(self.env)
        try:
            if name:
                link =  prov.get_link(name)
                if not link:
                    raise TracError('No such link name: ' + name)

                # prepare to modify
                req.hdf['admin.link'] = link.get_hash()
                req.hdf['admin.link.mode'] = 'modify'
                if req.method == 'POST':
                    # change value
                    if req.args.get('save'):
                        # set values
                        prov.modify(name,
                                    req.args.get('expose') != None,
                                    req.args.get('disp'),
                                    req.args.get('url'))
                        self._notify(req, "link '%s' is modified'" % name)
                    # redirect to base
                    req.redirect(base_href)
            else:
                if req.method == 'POST':
                    if req.args.get('add'):
                        # add new entry
                        name = req.args.get('name')
                        expose = req.args.get('expose') != None
                        url = req.args.get('url')
                        disp = req.args.get('disp')
                        req.hdf['admin.link'] = {'mode': 'add',
                                                 'name': name,
                                                 'exposed': expose,
                                                 'disp': disp,
                                                 'url': url}
                        prov.add(name, expose, disp, url)
                        self._notify(req, "link '%s' is added'" % name)
                    elif req.args.get('remove') and req.args.get('sel'):
                        # Remove components
                        sel = req.args.get('sel')
                        sel = isinstance(sel, list) and sel or [sel]
                        if not sel:
                            raise TracError, 'No item selected'
                        for name in sel:
                            prov.delete(name)
                        self._notify(req, 'deleted %d liks' % len(sel))
                    req.redirect(base_href)

        except Exception, e:
            self._error(req, str(e))
        
        # render current links
        links = []
        href = Href(base_href)
        for link in GeneralLinkSyntaxProvider(self.env).get_links():
            h = link.get_hash()
            h['href'] = href(link.get_name())
            links.append(h)
        req.hdf['admin.links'] = links
        # prepare notify message
        message_text, message_class = self._get_message(req)
        req.hdf['admin.message.text'] = message_text
        req.hdf['admin.message.class'] = message_class
        self._clear_message(req)
        add_stylesheet(req, 'admin/css/admin_link.css')
        return 'admin_link.cs', None


    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        """Return the htdocs directory.
        """
        from pkg_resources import resource_filename
        return [('admin', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the template directory.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
