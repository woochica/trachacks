# -*- coding: utf-8 -*-

# 2011 Steffen Hoffmann

"""Various classes and functions to provide backwards-compatibility with
previous versions of Python from 2.4 onward.
"""

# json was introduced in 2.6, use simplejson for older versions
# parse_qs was copied to urlparse and deprecated in cgi in 2.6
import sys
if sys.version_info[0] == 2 and sys.version_info[1] > 5:
    import json
    from urlparse import parse_qs
else:
    import simplejson as json
    from cgi import parse_qs

