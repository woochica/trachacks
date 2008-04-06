import os, sys

if os.environ['TRAC_VERSION'] in ('trunk', 'renderfilter'):
    import pkg_resources
    pkg_resources.require('Trac >= 0.11dev')

from trac.core import *
from trac.env import Environment
from trac.wiki.model import WikiPage
from trac.ticket.model import Ticket
from trac.web.href import Href
from genshi.core import *
from genshi.builder import tag

env = Environment(os.environ['TRAC'])
db = env.get_db_cnx()
cursor = db.cursor()

class FakeReq(object):
    def __init__(self):
        self.href = Href(os.environ['TRAC_VERSION'] + '/' + os.environ['TRAC'])
        self.authname = 'anonymous'
req = FakeReq()

from tracforge.admin.query import MultiQuery
q = MultiQuery(env, 'id!=0')
d = q.execute(req)
