import re
import time
from datetime import timedelta
from trac.core import Component, Interface, implements

# Interface

class IFieldHandler(Interface):
    """An extension point interface for adding field handlers. """
    
    def convert(self, req, field, record):
        """Converts the value and/or other attributes in the record."""


# Handlers

class NameHandler(Component):
    """'name' is not a normal attribute and so needs to be handled special."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        return record.name

class EpochHandler(Component):
    """Converts an epoch into a human-readable format.  Uses current
    time if empty."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        epoch = float(record.get(field) or time.time())
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(epoch))

class AgoEpochHandler(Component):
    """Converts an epoch into an 'n minutes ago..' type of message.
    Uses current time if empty."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        epoch = int(record.get(field) or time.time())
        ago = "%s ago" % timedelta(seconds=int(time.time()) - epoch)
        return ago

class NowHandler(Component):
    """Returns current time as an epoch if currently empty."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        epoch = float(record.get(field) or time.time())
        return epoch

class AuthorHandler(Component):
    """Returns the current author, if empty."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        author = record.get(field) or req.authname
        return author

class RunListHandler(Component):
    """Extract the role(s) from a run_list, which is the most accurate
    way to to determine a node's roles."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        role_re = re.compile(r"role\[([^\]]+)]")
        run_list = getattr(record, field, []) or record.get(field,[])
        roles = []
        for role in run_list:
            match = role_re.match(role)
            if match:
                roles.append(match.group(1))
        return ', '.join(roles)
    
class HttpHandler(Component):
    """Assemble an http link from the given port and the public_hostname
    fields."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        port = record.get(field,80)
        hostname = record.get('public_hostname','public_hostname-not-set-yet')
        url = 'http://%s:%s' % (hostname,port)
        return (url,url)
    
class HttpsHandler(Component):
    """Assemble an https link from the given port and the public_hostname
    fields."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        port = record.get(field,443)
        hostname = record.get('public_hostname','public_hostname-not-set')
        url = 'https://%s:%s' % (hostname,port)
        return (url,url)
    
class SshHandler(Component):
    """Assemble an ssh link from the the given host field."""
    implements(IFieldHandler)
    
    def convert(self, req, field, record):
        field = field.strip('_')
        hostname = record.get(field,'not-set-yet')
        url = 'ssh://' + hostname
        return (url,hostname)
