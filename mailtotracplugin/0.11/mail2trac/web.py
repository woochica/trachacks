"""
EmailPostHandler:
process email sent via a POST request
"""

from mail2trac.email2trac import mail2project
from trac.core import *
from trac.web.api import IRequestHandler

class EmailPostHandler(Component):

    implements(IRequestHandler)

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        match = req.path_info.strip('/') == 'mail2trac' and req.method == 'POST'
        if match:
            # XXX fix up the nonce so that anonymous POSTs are allowed
            req.args['__FORM_TOKEN'] = req.form_token
        return match

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
        message = req.args.get('message', '')
        if message:
            status = 200
            message = message.encode('utf-8')
            try:
                mail2project(self.env, message)
            except Exception, e:
                req.send(str(e), content_type='text/plain', status=500)
        else:
            status = 204
        req.send(message, content_type='text/plain', status=status)

        
