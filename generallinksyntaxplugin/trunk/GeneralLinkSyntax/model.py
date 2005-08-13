# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005 Shun-ichi Goto <gotoh@taiyo.co.jp>
#

import re
from trac.util import TracError

class LinkInfo:
    """Holder class of each general link information.
    """
    # internal variables
    expose = False
    disp = None
    url = None
    name = None
    name_re = re.compile(r'^\w+([-+_]\w+)*$', re.I)

    def __init__(self, name, expose, disp, url):
        if not name or name == '':
            raise TracError('Link name is required')
        if not url or len(url) == 0:
            raise TracError("'URL' is required")
        self.name = name
        self.disp = disp or name + ':%s'
        self.url = url
        self.expose = expose
        # validate 'name'
        if not self.name_re.search(name):
            raise TracError("Invalid link name: '%s'" % name)
        # validate 'disp'
        if 2 < len(self.disp.split('%s')):
            raise TracError("'Display' is allowed for at most one parameter")
        # validate 'URL' : URL may contains %xx chars
        if 2 < len(self.url.split('%s')):
            raise TracError("'URL' is allowed for at most one parameter")

    def __repr__(self):
        return '<%s %s>' % (__name__, self.name)

    def render(self, id=None, label=None):
        if not label:
            if id:
                parts = url.split('%s')
                if 1 < len(parts):
                    label = id.join(parts)
                else:
                    label = self.disp + ':' + id
            else:
                # no id specified
                label = self.disp
        # format URL with id
        # NOTE: Do not use format becuase URL may contain %xx.
        parts = url.split('%s')
        if 1 < len(parts):
            url = id.join(parts)
        else:
            url = self.url
        return '<a href="%s">%s</a>' % (url, label)

    # accessors
    
    def get_name(self):
        return self.name
    
    def get_expose(self):
        return self.expose

    def get_url(self):
        return self.url

    def get_disp(self):
        return self.disp

    def get_hash(self):
        return {'name': self.name,
                'expose': self.expose,
                'url': self.url,
                'disp': self.disp}


