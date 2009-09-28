"""
plugin for Trac to give anonymous users authenticated access
using a CAPTCHA
"""

# Plugin for trac 0.11

import random
import sys
import time
import urllib

from componentdependencies import IRequireComponents

from genshi.builder import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from skimpyGimpy import skimpyAPI

from trac.core import *
from trac.db import Table, Column
from trac.env import IEnvironmentSetupParticipant
from trac.web import IRequestFilter
from trac.web import ITemplateStreamFilter
from trac.web.api import IAuthenticator
from trac.web.auth import LoginModule
from trac.web.chrome import add_warning 
from trac.web.chrome import Chrome
from trac.web.chrome import INavigationContributor
from trac.web.chrome import ITemplateProvider
from trac.config import ListOption
from trac.config import Option

from tracsqlhelper import create_table
from tracsqlhelper import execute_non_query
from tracsqlhelper import get_scalar
from tracsqlhelper import get_table
from tracsqlhelper import insert_update

from utils import random_word
from web_ui import ImageCaptcha

try: 
    from acct_mgr.api import AccountManager
    from acct_mgr.web_ui import RegistrationModule
except:
    AccountManager = None

class AuthCaptcha(Component):

    ### class data
    implements(IRequestFilter, 
               ITemplateStreamFilter, 
               ITemplateProvider, 
               IAuthenticator, 
               IEnvironmentSetupParticipant, 
               IRequireComponents, 
               INavigationContributor
               )

    dict_file = Option('captchaauth', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")
    captcha_type = Option('captchaauth', 'type',
                          default="png")
    realms = ListOption('captchaauth', 'realms',
                        default="wiki, newticket")
    permissions = { 'wiki': [ 'WIKI_CREATE', 'WIKI_MODIFY' ],
                    'newticket': [ 'TICKET_CREATE' ] }

    xpath = { 'ticket.html': "//div[@class='buttons']" }
    delete = { 'ticket.html': "//div[@class='field']" }

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """

        if req.method == 'GET':
            if req.path_info.strip('/') in ['register', 'login'] and req.authname != 'anonymous':
                login_module = LoginModule(self.env)
                login_module._do_logout(req)
                req.redirect(req.href(req.path_info))


        if req.method == 'POST':

            realm = self.realm(req)

            # set the session data for name and email if CAPTCHA-authenticated
            if 'captchaauth' in req.args:
                name, email = self.identify(req)
                for field in 'name', 'email':
                    value = locals()[field]
                    if value:
                        req.session[field] = value
                req.session.save()
                if req.authname != 'anonymous' and realm == 'newticket':
                    req.args['author'] = name
                    if email:
                        req.args['author'] += ' <%s>' % email

            # redirect anonymous user posts that are not CAPTCHA-identified
            if req.authname == 'anonymous' and realm in self.realms:
                
                if 'captchaauth' in req.args and 'captchaid' in req.args:
                    # add warnings from CAPTCHA authentication
                    captcha = self.captcha(req)
                    if req.args['captchaauth'] != captcha:
                        add_warning(req, "You typed the wrong word. Please try again.")
                        try:
                            # delete used CAPTCHA
                            execute_non_query(self.env, "DELETE FROM captcha WHERE id=%s", req.args['captchaid'])
                        except:
                            pass

                    name, email = self.identify(req)
                    if not name:
                        add_warning(req, 'Please provide your name')
                    if AccountManager and name in AccountManager(self.env).get_users():
                        add_warning(req, '%s is already taken as by a registered user.  Please login or use a different name' % name)

                # redirect to previous location
                location = req.get_header('referer')
                if location:
                    location, query = urllib.splitquery(location)
                    
                    if realm == 'newticket':
                        args = [(key.split('field_',1)[-1], value)
                                for key, value in req.args.items()
                                if key.startswith('field_')]
                        location += '?%s' % urllib.urlencode(args)
                else:
                    location =  req.href()
                req.redirect(location)

        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
        
        Always returns a tuple of (template, content_type), even if
        unchanged.

        Note that `template`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """
        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
        return (template, data, content_type)

    
    ### ITemplateStreamFilter method

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        # only show CAPTCHAs for anonymous users
        if req.authname != 'anonymous':
            return stream

        # only put CAPTCHAs in the realms specified
        realm = self.realm(req)
        if realm not in self.realms:
            return stream

        # add the CAPTCHA to the stream
        if filename in self.xpath:

            # store CAPTCHA in DB and session
            word = random_word(self.dict_file)
            insert_update(self.env, 'captcha', 'id', req.session.sid, dict(word=word))
            req.session['captcha'] = word
            req.session.save()

            # render the template
            chrome = Chrome(self.env)
            template = chrome.load_template('captcha.html')
            _data = {}

            # CAPTCHA type
            if self.captcha_type == 'png':
                captcha = tag.img(None, src=req.href('captcha.png'))
            else:
                captcha = Markup(skimpyAPI.Pre(word).data())

            _data['captcha'] = captcha
            _data['email'] = req.session.get('email', '')
            _data['name'] = req.session.get('name', '')
            _data['captchaid'] = req.session.sid
            xpath = self.xpath[filename]
            stream |= Transformer(xpath).before(template.generate(**_data))
            if filename in self.delete:
                stream |= Transformer(self.delete[filename]).remove()

        return stream

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
        return [resource_filename(__name__, 'templates')]

    ### method for IAuthenticator

    """Extension point interface for components that can provide the name
    of the remote user."""

    def authenticate(self, req):
        """Return the name of the remote user, or `None` if the identity of the
        user is unknown."""

        # check for an authenticated user
        login_module = LoginModule(self.env)
        remote_user = login_module.authenticate(req)
        if remote_user:
            return remote_user

        # authenticate via a CAPTCHA
        if 'captchaauth' in req.args and 'captchaid' in req.args:

            # ensure CAPTCHA identification
            captcha = self.captcha(req)
            if captcha != req.args['captchaauth']:
                return 

            # ensure sane identity
            name, email = self.identify(req)
            if name is None:
                return
            if AccountManager and name in AccountManager(self.env).get_users():
                return

            # delete used CAPTCHA on success
            try:
                execute_non_query(self.env, "DELETE FROM captcha WHERE id=%s", req.args['captchaid'])
            except:
                pass

            # log the user in
            req.environ['REMOTE_USER'] = name
            login_module._do_login(req)

    ### methods for INavigationContributor

    """Extension point interface for components that contribute items to the
    navigation.
    """

    def get_active_navigation_item(self, req):
        """This method is only called for the `IRequestHandler` processing the
        request.
        
        It should return the name of the navigation item that should be
        highlighted as active/current.
        """
        return None

    def get_navigation_items(self, req):
        """Should return an iterable object over the list of navigation items to
        add, each being a tuple in the form (category, name, text).
        """
        if req.authname != 'anonymous' and 'captcha' in req.session:
            return [('metanav', '_login', tag.a("Login", 
                                               href=req.href.login())),
                    ('metanav', '_register', tag.a("Register",
                                                  href=req.href.register()))]
        return []

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        try:
            get_table(self.env, 'captcha')
        except:
            return True
        return False

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """

        # table of CAPTCHAs
        captcha_table = Table('captcha', key='key')[
            Column('id'),
            Column('word')]
        create_table(self.env, captcha_table)

    ### method for IRequireComponents
        
    def requires(self):
        """list of component classes that this component depends on"""
        return [ImageCaptcha]


    ### internal methods

    def identify(self, req):
        """
        identify the user, ensuring uniqueness (TODO);
        returns a tuple of (name, email) or success or None
        """
        name = req.args.get('name', None).strip()
        email = req.args.get('email', None).strip()
        return name, email
        

    def realm(self, req):
        """
        returns the realm according to the request
        """
        path = req.path_info.strip('/').split('/')
        if not path:
            return
        # TODO: default handler ('/')
        return path[0]

    def captcha(self, req):
        return get_scalar(self.env, "SELECT word FROM captcha WHERE id=%s", 0, req.args['captchaid'])
