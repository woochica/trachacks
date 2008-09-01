import sys
import os

import pkg_resources

try:
    pkg_resources.require('Trac')
except pkg_resources.DistributionNotFound:
    pass

from trac.core import *
from trac.env import Environment
from trac.wiki.model import WikiPage
from trac.ticket.model import Ticket
from genshi.core import *
from genshi.builder import tag

env = Environment(os.environ.get('TRAC', os.getcwd()))
db = env.get_db_cnx()
cursor = db.cursor()
