#!/usr/bin/env python
# found on trac google group:
# http://groups.google.com/group/trac-dev/browse_thread/thread/2c97c6c514487778?q=

import sys
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.mimeview import Context
from trac.wiki.formatter import HtmlFormatter
from trac.web.href import Href

env = EnvironmentStub()
req = Mock(href=Href('/'), abs_href=Href('http://www.example.com/'),
           authname='anonymous', perm=MockPerm(), args={})
context = Context.from_request(req, 'wiki')

if len(sys.argv) > 1:
    try:
        wiki = open(sys.argv[1]).read()
    except IOError:
        wiki = sys.argv[1] # parse it as tracwiki if not a file
else:
    wiki = '= The Trac Wiki to HTML converter ='

print '''
<html><head><link rel="stylesheet" href="trac.css" type="text/css" />
</head><body>
'''
print HtmlFormatter(env, context, wiki).generate()

print '''
</body>
</html>
'''