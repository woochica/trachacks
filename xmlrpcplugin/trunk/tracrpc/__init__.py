from tracrpc.api import *
from tracrpc.web_ui import *
from tracrpc.ticket import *
from tracrpc.wiki import *
from tracrpc.search import *

__author__ = 'Alec Thomas <alec@swapoff.org>'
__license__ = 'BSD'

try:
    __version__ = __import__('pkg_resources').get_distribution('TracXMLRPC').version
except (ImportError, pkg_resources.DistributionNotFound):
    pass
