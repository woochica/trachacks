# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from tracrpc.api import *
from tracrpc.json_rpc import *
from tracrpc.xml_rpc import *
from tracrpc.web_ui import *
from tracrpc.ticket import *
from tracrpc.wiki import *
from tracrpc.search import *

__author__ = ['Alec Thomas <alec@swapoff.org>',
              'Odd Simon Simonsen <simon-code@bvnetwork.no>']
__license__ = 'BSD'

try:
    __version__ = __import__('pkg_resources').get_distribution('TracXMLRPC').version
except (ImportError, pkg_resources.DistributionNotFound):
    pass
