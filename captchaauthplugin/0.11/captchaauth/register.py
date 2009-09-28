"""
A quick and dirty captcha for use with AccountManagerPlugin registration
"""
# Plugin for trac 0.11

from acct_mgr.web_ui import RegistrationModule

from componentdependencies import IRequireComponents

from genshi.builder import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from skimpyGimpy import skimpyAPI

from trac.config import Option
from trac.core import *
from trac.web import IRequestFilter
from trac.web import ITemplateStreamFilter
from trac.web.api import IRequestHandler
from trac.web.chrome import add_warning 

from utils import random_word
from web_ui import ImageCaptcha

class RegistrationCaptcha(Component):

    ### class data
    implements(IRequestFilter, ITemplateStreamFilter, IRequireComponents)
    dict_file = Option('captchaauth', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")
    captcha_type = Option('captchaauth', 'type',
                          default="png")


    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """

        if req.path_info.strip('/') == "register":

            if req.method == "POST":
                correct_answer = req.session.pop('captcha', None)
                req.session.save()
                if req.args['captcha'].lower() != correct_answer:
                    req.session['captchaauth_message'] = "You typed the wrong word. Please try again."
                    req.session.save()
                    req.redirect(req.href('register'))
            if req.method == "GET":
                message = req.session.pop('captchaauth_message', None)
                if message:
                    add_warning(req, message)
                                    
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
        # move these someplace sensible?
        form_id = "acctmgr_registerform" # id of the registration form
        msg = "Please enter the text below to prove you're not a machine."

        if filename == "register.html":
            word = random_word(self.dict_file)
            req.session['captcha'] = word
            req.session.save()
            if self.captcha_type == 'png':
                captcha = '<img src="%s"/>' % req.href('captcha.png')
            else:
                captcha = skimpyAPI.Pre(word).data()
            content = "<p>%s</p><p>%s</p>" % (msg, captcha)
            content += '<label>Confirm: <input type="text" name="captcha" class="textwidget" size="20"/></label>'
            stream |= Transformer('//form[@id="%s"]/fieldset[1]' % form_id).append(tag.div(Markup(content)))

        return stream

    ### method for IRequireComponents

    def requires(self):
        """list of component classes that this component depends on"""
        return [ImageCaptcha, RegistrationModule]
