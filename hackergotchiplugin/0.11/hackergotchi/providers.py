# Created by Noah Kantrowitz on 2008-05-16.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import urllib
from cStringIO import StringIO
try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

from trac.core import *
from trac.config import Option, BoolOption
from trac.web.api import IRequestHandler, RequestDone

from hackergotchi.api import IHackergotchiProvider
try:
    from hackergotchi.identicon import render_identicon
except ImportError:
    render_identicon = None

# TODO: Add a client-side identicon implementation using canvas <NPK>

class GravatarHackergotchiProvider(Component):
    """Use gravatar.com to provide images."""
    
    implements(IHackergotchiProvider)
    
    default = Option('hackergotchi', 'gravatar_default', default='identicon',
                     doc='The default value to pass along to gravatar to use if the email address does not match.')
    
    # IHackergotchiProvider methods
    def get_hackergotchi(self, href, user, name, email):
        if email:
            return 'http://www.gravatar.com/avatar.php?' + urllib.urlencode({
                'gravatar_id': md5(email).hexdigest(),
                'default': self.default,
                'size': 20,
            })


class IdenticonHackergotchiProvider(Component):
    """Generate identicons locally to provide images."""
    
    implements(IHackergotchiProvider, IRequestHandler)
    
    # IHackergotchiProvider methods
    def get_hackergotchi(self, href, user, name, email):
        if render_identicon is None:
            return None
        
        h = md5(user)
        h.update(name or '')
        h.update(email or '')
        code = h.hexdigest()[:8]
        return href.identicon(code+'.png')
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/identicon')

    def process_request(self, req):
        if render_identicon is None:
            raise TracError('PIL not installed, can not render identicon')
        
        # Render the identicon to a string
        code = int(req.path_info[11:-4], 16)
        icon = render_identicon(code, 20)
        out = StringIO()
        icon.save(out, 'png')
        data = out.getvalue()
        
        # Send response
        req.send_response(200)
        req.send_header('Content-Type', 'image/png')
        req.send_header('Content-Length', len(data))
        req.send_header('Cache-Control', 'max-age=36000')
        if req.method != 'HEAD':
            req.write(data)
        raise RequestDone