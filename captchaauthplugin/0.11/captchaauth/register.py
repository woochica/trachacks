"""
A quick and dirty captcha for use with AccountManagerPlugin
"""
# Plugin for trac 0.11

import random
import sys
import time
import urllib

from genshi.builder import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from skimpyGimpy import skimpyAPI

from trac.core import *
from trac.web import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web import ITemplateStreamFilter
from trac.web.chrome import add_warning 
from trac.config import Option
from trac.config import PathOption

class RegistrationCaptcha(Component):

    ### class data
    implements(IRequestFilter, ITemplateStreamFilter, IRequestHandler)
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

    
    ### methods for IRequestHandler

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        if self.captcha_type == 'png' and req.path_info.strip('/') == 'captcha.png' and 'captcha' in req.session:
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
        img = skimpyAPI.Png(req.session['captcha']).data()
#        img = skimpyAPI.Png(req.session['captcha'], scale=2.7).data()
        req.send(img, 'image/png')


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
            word = self.random_word()
            req.session['captcha'] = word
            req.session.save()
            if self.captcha_type == 'png':
                captcha = '<img src="%s"/>' % req.href('captcha.png')
            else:
                captcha = self.skimpy_pre_captcha(word)
            content = "<p>%s</p><p>%s</p>" % (msg, captcha)
            content += "<label>Confirm: <input type='text' name='captcha' class='textwidget' size='20'></label>"
            stream |= Transformer('//form[@id="%s"]/fieldset[1]' % form_id).append(tag.div(Markup(content)))

        return stream


    ### internal methods

    def skimpy_pre_captcha(self, passphrase):
        """ Return HTML content of captcha as string """
        return skimpyAPI.Pre(passphrase).data()
                                       
    def skimpy_png_captcha(self, passphrase):
        pass

    def random_word(self):
        """ Return a random word for use with the captcha """
        min_len =  5
        
        if not globals().has_key('captcha_dict'):
            if self.dict_file.startswith("http://"):
                f = urllib.urlopen(self.dict_file)
            else:
                f = open(self.dict_file, "r")
            _dict = f.read()
            f.close()
            _dict = _dict.lower().split()
            _dict = [word for word in _dict if word.isalpha() and len(word) > min_len]
            globals()['captcha_dict'] = _dict

        return random.Random().choice(captcha_dict)
