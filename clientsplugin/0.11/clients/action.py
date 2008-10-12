from lxml import etree
from trac.core import *

class IClientActionProvider(Interface):
  """Extension point interface for components that define their own way
  to act on a given client summary (IClientSummaryProvider.get_summary
  """

  def get_name():
    """Return the name of the action (for use in UI)
    """

  def get_description():
    """Return the description of the action (for use in UI)
    """

  def options(client=None):
    """The options for this action
       If the client option is None then these options are defined as being per instance.
    """

  def init(event, client):
    """Todo
    """

  def perform(req, summary):
    """Perform the action. This must return an etree object
    """
