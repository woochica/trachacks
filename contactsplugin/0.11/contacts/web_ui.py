from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import add_script, add_stylesheet, INavigationContributor, ITemplateProvider
from trac.perm import IPermissionRequestor
from trac.util.translation import _

from genshi.builder import tag

from pkg_resources import resource_filename
import re

from model import Contact, ContactIterator

class ContactsAdminPanel(Component):
    """ Pages for adding/editing contacts. """
    implements(INavigationContributor, ITemplateProvider, IRequestHandler, IPermissionRequestor)

    #   INavigationContributor methods
    def get_active_navigation_item(self, req):
        """This method is only called for the `IRequestHandler` processing the
        request.
        
        It should return the name of the navigation item that should be
        highlighted as active/current.
        """
        return 'contacts'
    def get_navigation_items(self, req):
        """Should return an iterable object over the list of navigation items to
        add, each being a tuple in the form (category, name, text).
        """
        if 'CONTACTS_VIEW' in req.perm('contacts'):
            yield('mainnav', 'contacts', tag.a(_('Contacts'), href=req.href.contacts()))

    #   ITemplateProvider
    def get_htdocs_dirs(self):
        return [('contacts', resource_filename('contacts', 'htdocs'))]
    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [resource_filename('contacts', 'templates')]

    #   IRequestHandler methods
    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        if re.match(r'^/contact', req.path_info):
            return True
    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        req.perm('contacts').assert_permission('CONTACTS_VIEW')

        add_stylesheet(req, 'common/css/admin.css')
        if re.match(r'^/contacts$', req.path_info):
            return ('contacts.html', 
                {   'contacts': ContactIterator(self.env),
                    'can_edit': 'CONTACTS_ADMIN' in req.perm('contacts')
                }, None)

        req.perm('contacts').assert_permission('CONTACTS_ADMIN')

        #   We will be using the contact.html file, so include it's JS
        #   Get Contact ID
        params = req.path_info.split('/')
        contact_id = None
        if (len(params) > 2 and params[2].isdigit()):
            contact_id = params[2]
        contact = Contact(self.env, contact_id)

        #   Check if saving
        if req.method == 'POST' and req.args.get('addcontact'):
            contact.update_from_req(req)
            contact.save()
            if (req.args.get('redirect')):
                req.redirect(req.args.get('redirect') + '?contact_id=%d' % contact.id)
            else:
                req.redirect(req.href.contacts())
            #   redirecting, so the rest of this function does not get ran

        template = {'contact': contact}
        if (len(params) > 2 and params[2].isdigit()):
            add_script(req, 'contacts/edit_contact.js')
            add_stylesheet(req, 'contacts/edit_contact.css')
            template['title'] = 'Edit %s' % contact.last_first()
            template['edit'] = True
        else:
            template['title'] = 'Add Contact'
            template['edit'] = False
        if (req.args.get('redirect')):
            template['redirect'] = req.args.get('redirect')
        else:
            template['redirect'] = None

        return ('contact.html', template, None)

    #   IPermissionRequest methods
    def get_permission_actions(self):
        """Return a list of actions defined by this component.
        
        The items in the list may either be simple strings, or
        `(string, sequence)` tuples. The latter are considered to be "meta
        permissions" that group several simple actions under one name for
        convenience.
        """
        return ['CONTACTS_VIEW', ('CONTACTS_ADMIN', ['CONTACTS_VIEW'])]
