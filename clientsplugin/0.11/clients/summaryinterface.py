from lxml import etree
from trac.core import *

class IClientSummaryProvider(Interface):
  """Extension point interface for components that their own way
  to summarise a given client.
  """

  def __init__(env, req, debug = False):
    """Constructor
    """

  def get_name():
    """Return the name of the summary (for use in UI)
    """

  def get_description():
    """Return the description of the summary (for use in UI)
    """

  def get_summary(client, fromdate = None, todate = None):
    """Get the summary. This must return an etree object
    """
