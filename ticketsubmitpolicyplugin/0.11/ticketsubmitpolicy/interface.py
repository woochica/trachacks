from trac.core import Interface

class ITicketSubmitPolicy(Interface):
    """interface for ticket submission policy enforcers"""

    def name():
        """name of the policy"""

    def javascript():
        """returns javascript functions"""

    def onload(policy, condition, *args):
        """returns code to be executable on page load"""

    def onsubmit(policy, condition, *args):
        """returns code to be executed on form submission"""

    def filter_stream(stream, policy, condition, *args):
        """filter the stream and return it"""
