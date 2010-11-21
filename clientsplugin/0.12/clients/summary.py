from lxml import etree
from trac.core import *

class IClientSummaryProvider(Interface):
  """Extension point interface for components that define their own way
  to summarise a given client.
  """

  def get_name():
    """Return the name of the summary (for use in UI)
    """

  def get_description():
    """Return the description of the summary (for use in UI)
    """

  def options(client=None):
    """Return a series of tupoles defining the options
    """

  def init(event, client):
    """Initialise the summary for a specific instance and client combo
    """

  def get_summary(req, fromdate = None, todate = None):
    """Get the summary. This must return an etree object
    """
