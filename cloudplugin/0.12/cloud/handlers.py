import re
import time
from datetime import timedelta
from trac.core import Component, Interface, implements

# Interface

class IFieldHandler(Interface):
    """An extension point interface for adding field handlers. """
    
    def convert_item(self, field, item, req):
        """Converts a PyChef item's attribute value for viewing."""
    
    def convert_req(self, field, req):
        """Converts a web request to a PyChef attribute value for saving."""


# Handlers

class DefaultHandler(Component):
    """Default field handler."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        if hasattr(item.attributes, 'get_dotted'):
            return item.attributes.get_dotted(field)
        else:
            return item[field]
    
    def convert_req(self, field, req):
        return req.args.get(field)

class NameHandler(DefaultHandler):
    """'name' is not a normal attribute and so needs special handling."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        return item.name

class EpochHandler(DefaultHandler):
    """Converts an epoch into a human-readable format and vice-versa.
    Uses current time if no item is provided or the req's value is empty."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        epoch = item and float(item.attributes.get_dotted(field)) or time.time()
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.localtime(epoch))
    
    def convert_req(self, field, req):
        try:
            value = req.args.get(field)
            t = time.strptime(value, "%Y-%m-%d %H:%M:%S UTC")
            epoch = time.mktime(t)
        except:
            epoch = time.time()
        return epoch

class AgoEpochHandler(DefaultHandler):
    """Converts an epoch into an 'n minutes ago..' type of message."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        epoch = int(item.attributes.get_dotted(field))
        ago = "%s ago" % timedelta(seconds=int(time.time()) - epoch)
        return ago

class AuthorHandler(DefaultHandler):
    """Returns the current author if no item is provided."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        author = item and item.attributes.get_dotted(field) or req.authname
        return author

class RunListHandler(DefaultHandler):
    """Extract the role(s) from a run_list, which is the most accurate
    way to to determine a node's roles."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        role_re = re.compile(r"role\[([^\]]+)]")
        run_list = getattr(item, field, []) or item.attributes.get_dotted(field)
        roles = []
        for role in run_list:
            match = role_re.match(role)
            if match:
                roles.append(match.group(1))
        return ', '.join(roles)
    
    def convert_req(self, field, req):
        roles = req.args.get('run_list')
        if not roles:
            return []
        if isinstance(roles,str) or isinstance(roles,unicode):
            roles = [roles]
        return ["role[%s]" % r for r in roles]
    
class HttpHandler(DefaultHandler):
    """Assemble an http link from the given hostname field."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        hostname = item.attributes.get_dotted(field)
        url = 'http://' + hostname
        return (url,url)
    
class HttpsHandler(DefaultHandler):
    """Assemble an https link from the given hostname field."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        hostname = item.attributes.get_dotted(field)
        url = 'https://' + hostname
        return (url,url)
    
class HttpPortHandler(DefaultHandler):
    """Assemble an http link from the given port and ec2.public_hostname."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        port = item.attributes.get_dotted(field)
        try:
            hostname = item.attributes.get_dotted('ec2.public_hostname')
        except KeyError:
            hostname = item.attributes.get_dotted('public_hostname')
        url = 'http://%s:%s' % (hostname,port)
        return (url,url)
    
class HttpsPortHandler(DefaultHandler):
    """Assemble an https link from the given port and ec2.public_hostname."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        port = item.attributes.get_dotted(field)
        try:
            hostname = item.attributes.get_dotted('ec2.public_hostname')
        except KeyError:
            hostname = item.attributes.get_dotted('public_hostname')
        url = 'https://%s:%s' % (hostname,port)
        return (url,url)
    
class SshHandler(DefaultHandler):
    """Assemble an ssh link from the the given host field."""
    implements(IFieldHandler)
    
    def convert_item(self, field, item, req):
        hostname = item.attributes.get_dotted(field)
        url = 'ssh://' + hostname
        return (url,hostname)
