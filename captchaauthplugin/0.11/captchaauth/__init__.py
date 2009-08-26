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
from trac.web import ITemplateStreamFilter
from trac.web.chrome import add_warning 
from trac.config import PathOption

class CaptchaauthPlugin(Component):
    implements(IRequestFilter, ITemplateStreamFilter)

    dict_file = PathOption('captchaauth', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")


    # IRequestFilter methods
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

    # ITemplateStreamFilter methods
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
            key = random.Random().randint(0, sys.maxint)
            word = self.random_word()
            req.session['captcha'] = word
            req.session.save()
            content = "<p>%s</p>%s" % (msg, self.skimpy_captcha(word))
            content += "<label>Confirm: <input type='text' name='captcha' class='textwidget' size='20'></label>"
            stream |= Transformer('//form[@id="%s"]/fieldset[1]' % form_id).append(tag.div(Markup(content)))

        return stream

    # helpers
    def skimpy_captcha(self, passphrase):
        """ Return HTML content of captcha as string """
        return skimpyAPI.Pre(passphrase).data()
                                       
    def random_word(self):
        """ Return a random word for use with the captcha """
        min_len =  5
        
        if not globals().has_key('captcha_dict'):
            if self.dict_file.startswith("http://"):
                f = urllib.urlopen(self.dict_file)
            else:
                f = open(dict_file, "r")
            _dict = f.read()
            f.close()
            _dict = _dict.lower().split()
            _dict = [word for word in _dict if word.isalpha() and len(word) > min_len]
            globals()['captcha_dict'] = _dict

        return random.Random().choice(captcha_dict)
