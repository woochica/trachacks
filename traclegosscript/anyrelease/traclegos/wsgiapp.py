"""
paste app factory
"""
import logging
import os
import sys

from paste.httpexceptions import HTTPExceptionHandler
from traclegos.web import View

def str2list(string):
    """returns a list from a comma-separated string"""
    # XXX this could go in a utils.py file
    return [ i.strip() for i in string.split(',') if i.strip() ]

def make_app(global_conf, **app_conf):
    """create the traclegos view and wrap it in middleware"""
    key_str = 'traclegos.'

    # constructor arguments
    list_items = [ 'conf', 'site_templates', 
                   'available_templates', 'available_repositories',
                   'available_databases' ]
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])
    for item in list_items:
        if args.has_key(item):
            args[item] = str2list(args[item])

    # variables
    args['variables'] = dict([(key.split(key_str, 1)[-1], value)
                              for key, value in global_conf.items()
                              if key.startswith(key_str) ])

    app = View(**args)
    return HTTPExceptionHandler(app)

try:

    from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
    from repoze.who.plugins.htpasswd import HTPasswdPlugin
    from repoze.who.plugins.form import RedirectingFormPlugin
    from repoze.who.middleware import PluggableAuthenticationMiddleware
    from acct_mgr.pwhash import htpasswd

    def check(password, hashed):
        """check callback for AccountManager's htpasswd"""
        return hashed == htpasswd(password, hashed)

    def make_auth_app(global_conf, **app_conf):
        """example authenticated app with an htpasswd file"""
        
        assert 'auth.htpasswd' in app_conf
        assert os.path.exists(app_conf['auth.htpasswd'])
        
        app_conf['traclegos.auth'] = True

        # make the app
        app = make_app(global_conf, **app_conf)

        # wrap in repoze.who authentication middleware
        htpasswd_auth = HTPasswdPlugin(app_conf['auth.htpasswd'], check)
        auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
        form = RedirectingFormPlugin('/', '/login', '/logout', 'auth_tkt')
        identifiers = [('form', form), ('auth_tkt', auth_tkt)]
        authenticators = [('htpasswd_auth', htpasswd_auth)]
        challengers = [('form', form)]

        from repoze.who.classifiers import default_request_classifier
        from repoze.who.classifiers import default_challenge_decider
        log_stream = None

        return PluggableAuthenticationMiddleware(app, 
                                                 identifiers,
                                                 authenticators,
                                                 challengers,
                                                 [],
                                                 default_request_classifier,
                                                 default_challenge_decider,
                                                 log_stream=None,
                                                 log_level=logging.DEBUG)

except ImportError:
    pass
