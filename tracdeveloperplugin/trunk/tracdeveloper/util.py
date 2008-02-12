# -*- coding: utf-8 -*-

import re

from genshi import HTML

def linebreaks(value):
    """Converts newlines in strings into <p> and <br />s."""
    if not value:
        return ''
    value = re.sub(r'\r\n|\r|\n', '\n', value) # normalize newlines
    paras = re.split('\n{2,}', value)
    paras = ['<p>%s</p>' % p.strip().replace('\n', '<br />') for p in paras]
    return HTML(''.join(paras))
