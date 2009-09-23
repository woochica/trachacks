"""
PNG image CAPTCHA handler
"""

from genshi.builder import tag

from skimpyGimpy import skimpyAPI

from trac.config import Option
from trac.core import *
from trac.web import IRequestHandler

class ImageCaptcha(Component):

    implements(IRequestHandler)
    captcha_type = Option('captchaauth', 'type',
                          default="png")


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
        img = skimpyAPI.Png(req.session['captcha'], scale=2.2).data()
        req.send(img, 'image/png')

