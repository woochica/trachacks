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

wiki = '= Trac Wiki to HTML Demo ='

print HtmlFormatter(env, context, wiki).generate()