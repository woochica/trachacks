import os, sys

if os.environ['TRAC_VERSION'] in ('trunk', 'renderfilter', '0.11-stable'):
    import pkg_resources
    pkg_resources.require('Trac >= 0.11dev')

from trac.core import *
from trac.env import Environment
from trac.wiki.model import WikiPage
from trac.ticket.model import Ticket
from genshi.core import *
from genshi.builder import tag

env = Environment(os.environ['TRAC'])
db = env.get_db_cnx()
cursor = db.cursor()
