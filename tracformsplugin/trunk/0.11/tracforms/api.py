# -*- coding: utf-8 -*-

from genshi.builder import tag
from pkg_resources import resource_filename
from urllib import unquote_plus

from trac.core import Component, ExtensionPoint, Interface, implements
from trac.perm import IPermissionRequestor
from trac.resource import IResourceManager, Resource, ResourceNotFound, \
                          get_resource_name, get_resource_shortname, \
                          get_resource_url

# Import i18n methods.  Fallback modules maintain compatibility to Trac 0.11
# by keeping Babel optional here.
try:
    from trac.util.translation import domain_functions
    add_domain, _, ngettext, tag_ = \
        domain_functions('tracforms', ('add_domain', '_', 'ngettext', 'tag_'))
except ImportError:
    from genshi.builder import tag as tag_
    from trac.util.translation import gettext
    _ = gettext
    ngettext = _
    def add_domain(a,b,c=None):
        pass

from trac.web import IRequestHandler
from trac.web.api import HTTPBadRequest, HTTPUnauthorized

# Import AccountManagerPlugin methods, if plugin is installed.
try:
    from acct_mgr.api import IPasswordStore
    can_check_user = True
except ImportError:
    can_check_user = False

from compat import json


class IFormChangeListener(Interface):
    """Extension point interface for components that require notification
    when TracForms forms are created, modified or deleted.
    """

    def form_created(form):
        """Called when a form is created."""

    def form_changed(form, author, old_state):
        """Called when a form is modified.

        `old_state` is a dictionary containing the previous values of the
        fields that have changed.
        """

    def form_deleted(form):
        """Called when a form is deleted."""
    # DEVEL: not implemented yet


class IFormDBObserver(Interface):
    def get_tracform_ids(self, src, cursor=None):
        pass

    def get_tracform_meta(self, src, cursor=None):
        pass

    def get_tracform_state(self, src, cursor=None):
        pass

    def get_tracform_history(self, src, cursor=None):
        pass

    def save_tracform(self, src, state, updater,
                        base_version=None, keep_history=False,
                        track_fields=False, cursor=None):
        pass

    def get_tracform_fields(self, src, cursor=None):
        pass

    def get_tracfrom_fieldinfo(self, src, field, cursor=None):
        pass

    def reset_tracform(self, src, field=None, author=None, cursor=None):
        pass

    def search_tracforms(self, env, terms, cursor=None):
        pass


def tracob_first(fn=None, default=None):
    if fn is None:
        def builder(fn):
            return tracob_first(fn, default)
        return builder
    else:
        def wrapper(self, *_args, **_kw):
            observers = fn(self, *_args, **_kw)
            for observer in observers:
                result = getattr(observer, fn.__name__)(*_args, **_kw)
                if result is not default:
                    return result
            else:
                return default
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper


class FormDBUser(Component):
    tracformdb_observers = ExtensionPoint(IFormDBObserver)

    @tracob_first
    def save_tracform(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_ids(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_meta(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_state(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_history(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_fields(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_fieldinfo(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def reset_tracform(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def search_tracforms(self, *_args, **_kw):
        return self.tracformdb_observers


class FormBase(Component):
    """Provides i18n support for TracForms."""

    def __init__(self):
        # bind 'tracforms' catalog to specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)


class FormSystem(FormBase, FormDBUser):
    """Provides permissions and access to TracForms as resource 'form'."""

    implements(IPermissionRequestor, IResourceManager)

    # IPermissionRequestor method

    def get_permission_actions(self):
        return ['FORM_VIEW', 'FORM_EDIT_VAL', 'FORM_RESET',
                ('FORM_ADMIN', ['FORM_VIEW', 'FORM_EDIT_VAL', 'FORM_RESET'])]

    # IResourceManager methods

    def get_resource_realms(self):
        yield 'form'

    def get_resource_description(self, resource, format=None, **kwargs):
        env = self.env
        href = kwargs.get('href')
        if resource.parent is None:
            return _("Unparented form %(id)s", id=resource.id)
        parent_name = get_resource_name(env, resource.parent)
        parent_url = href and \
                     get_resource_url(env, resource.parent, href) or None
        parent = parent_url is not None and \
                 tag.a(parent_name, href=parent_url) or parent_name
        # DEVEL: resource description not implemented yet
        #if format == 'summary':
        #    return Form(self.env, resource).description
        if resource.id:
            if format == 'compact':
                return _("Form %(form_id)s (%(parent)s)", form_id=resource.id,
                         parent=get_resource_shortname(env, resource.parent))
            # TRANSLATOR: Most verbose title, i.e. for form history page
            return tag_("Form %(form_id)s (in %(parent)s)",
                        form_id=resource.id, parent=parent)
        else:
            # TRANSLATOR: Title printed i.e. in form select page
            if format == 'compact':
                return tag_("Forms (%(parent)s)", parent=parent)
            return tag_("Forms in %(parent)s", parent=parent)

    def get_resource_url(self, resource, href, **kwargs):
        # use parent's url instead
        return get_resource_url(self.env, resource.parent, href)        

    def resource_exists(self, resource):
        try:
            if get_tracform_meta(resource.id)[1] is not None:
               return True
        except ResourceNotFound:
            return False


class PasswordStoreUser(Component):
    if can_check_user:
        passwordstore_observers = ExtensionPoint(IPasswordStore)

        @tracob_first
        def has_user(self, *_args, **_kw):
            return self.passwordstore_observers
    else:
        def has_user(self, *_args, **_kw):
            """Stub, if AccountManagerPlugin isn't installed."""
            return False


class FormUpdater(FormDBUser, PasswordStoreUser):
    """Update request handler for TracForms form commits."""

    implements(IRequestHandler)

    def match_request(self, req):
        return req.path_info.endswith('/formdata/update')

    def process_request(self, req):
        req.perm.require('FORM_EDIT_VAL')
        try:
            self.log.debug('UPDATE ARGS:' + str(req.args))
            args = dict(req.args)
            backpath = args.pop('__backpath__', None)
            context = json.loads(
                unquote_plus(args.pop('__context__', None)) or \
                '(None, None, None)')
            basever = args.pop('__basever__', None)
            keep_history = args.pop('__keep_history__', None)
            track_fields = args.pop('__track_fields__', None)
            args.pop('__FORM_TOKEN', None)  # Ignore.
            if context is None:
                # TRANSLATOR: HTTP error message
                raise HTTPBadRequest(_("__context__ is required"))
            who = req.authname
            result = json.dumps(args, separators=(',', ':'))
            self.save_tracform(context, result, who, basever,
                                keep_history=keep_history,
                                track_fields=track_fields)
            if backpath is not None:
                req.send_response(302)
                req.send_header('Content-Type', 'text/plain')
                req.send_header('Location', backpath)
                req.send_header('Content-Length', len('OK'))
                req.end_headers()
                req.write('OK')
            else:
                req.send_response(200)
                req.send_header('Content-Type', 'text/plain')
                req.send_header('Content-Length', len('OK'))
                req.end_headers()
                req.write('OK')
        except Exception, e:
            req.send_response(500)
            req.send_header('Content-type', 'text/plain')
            req.send_header('Content-Length', len(str(e)))
            req.end_headers()
            req.write(str(e))

