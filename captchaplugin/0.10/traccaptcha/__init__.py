from pickle import loads, dumps
from trac.core import *
from trac.config import *
from trac.web.chrome import ITemplateProvider
from trac.web.api import IRequestFilter, IRequestHandler


class ICaptchaGenerator(Interface):
    """ An captcha implementation. """
    def generate_captcha(req):
        """ Return a tuple of `(result, html)`, where `result` is the expected
        response and `html` is a HTML fragment for displaying the captcha
        challenge. """


class FakeRequest(object):
    def __init__(self, req, path_info):
        object.__setattr__(self, '_req', req)
        object.__setattr__(self, '_fake_path_info', path_info)

    def __setattr__(self, key, value):
        return setattr(self._req, key, value)

    def __getattr__(self, key):
        if key == 'path_info':
            return self._fake_path_info
        if key == 'method':
            return 'POST'
        return getattr(self._req, key)


class Intercept(object):
    """ Intercepts POSTs at request processing time, once the session is
    valid. """
    def __init__(self, proxied):
        object.__setattr__(self, '_proxied', proxied)

    def __getattr__(self, key):
        return getattr(self._proxied, key)
        
    def __setattr__(self, key, value):
        return setattr(self._proxied, key, value)

    def process_request(self, req):
        if req.method == 'POST' and not int(req.session.get('captcha_verified', 0)):
            req.session['captcha_form_state'] = dumps(dict([(k, v) for k, v in req.args.items()])).decode('utf-8')
            req.session['captcha_path_info'] = req.path_info
            req.redirect(req.href('/captcha'))
        return self._proxied.process_request(req)


class TracCaptchaPlugin(Component):
    implements(ITemplateProvider, IRequestHandler, IRequestFilter)

    request_handlers = ExtensionPoint(IRequestHandler)
    restrict_to = ListOption('captcha', 'restrict_to', 'wiki, ticket',
        """ Modules to restrict POST interception to. """)
    captcha = ExtensionOption('captcha', 'captcha', ICaptchaGenerator,
                              'ExpressionCaptcha', """ Captcha generator to use. """)
    trust_authenticated = BoolOption('spam-filter', 'trust_authenticated', 'true',
        """Whether content submissions by authenticated users should be trusted
        without checking for potential spam or other abuse.""")


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/captcha'
    
    def process_request(self, req):
        if req.method == 'POST':
            self.env.log.debug('Captcha response: %s (expected %s)' % 
                (req.args['captcha_response'], req.session['captcha_expected']))
            if req.args['captcha_response'] == req.session['captcha_expected']:
                req.session['captcha_verified'] = 1
                args = loads(req.session['captcha_form_state'].encode('utf-8'))
                req = FakeRequest(req, req.session['captcha_path_info'])
                for k, v in args.iteritems():
                    req.args[k] = v
                for request_handler in self.request_handlers:
                    if request_handler.match_request(req):
                        return request_handler.process_request(req)
                raise TracError('Could not locate original request handler for %s' % req.path_info)
            else:
                req.hdf['error'] = 'Captcha verification failed'
        result, html = self.captcha.generate_captcha(req)
        req.hdf['captcha.challenge'] = html
        req.hdf['captcha.href'] = req.href('captcha')
        req.session['captcha_expected'] = result
        req.session.save()
        return 'captcha.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """ Return the absolute path of the directory containing the provided
        ClearSilver templates.  """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # TODO Allow restrict_to to specify request paths to allow
        if not self.trust_authenticated and req.method == 'POST' \
                and handler is not self:
            return Intercept(handler)
        return handler

    def post_process_request(self, req, template, content_type):
        return (template, content_type)
