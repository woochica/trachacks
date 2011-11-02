"""
Trac mail filters
"""

from mail2trac.interface import IEmailHandler
from trac.core import *
from utils import strip_quotes

class RemoveQuotes(Component):
    """removes reply quotes from email (or tries to, anyway)"""

    implements(IEmailHandler)

    def match(self, message):
        return False

    def invoke(self, message, warnings):
        payload = message.get_payload()
        if isinstance(payload, basestring):
            if message.get('Content-Disposition', 'inline') == 'inline' and message.get_content_maintype() == 'text':
                message.set_payload(strip_quotes(payload))
        else:
            for _message in payload:
                self.invoke(_message, warnings)
        return message
