from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, escape
import time

class DownloadsApi(object):

    def __init__(self, component):
        self.env = component.env
        self.log = component.log

    # Get list functions

    # Get one item functions

    # Add item functions

    # Edit item functions

    # Delete item functions
