from trac.core import *
from trac.perm import IPermissionRequestor
import inspect
import types
import xmlrpclib
try:
    set = set
except:
    from sets import Set as set

RPC_TYPES = {int: 'int', bool: 'boolean', str: 'string', float: 'double',
             xmlrpclib.DateTime: 'dateTime.iso8601', xmlrpclib.Binary: 'base64',
             list: 'array', dict: 'struct', None : 'int'}


def expose_rpc(permission, return_type, *arg_types):
    """ Decorator for exposing a method as an RPC call with the given
    signature. """
    def decorator(func):
        if not hasattr(func, '_xmlrpc_signatures'):
            func._xmlrpc_signatures = []
            func._xml_rpc_permission = permission
        func._xmlrpc_signatures.append((return_type,) + tuple(arg_types))
        return func
    return decorator


class IXMLRPCHandler(Interface):
    def xmlrpc_namespace():
        """ Provide the namespace in which a set of methods lives.
            This can be overridden if the 'name' element is provided by
            xmlrpc_methods(). """

    def xmlrpc_methods():
        """ Return an iterator of (permission, signatures, callable[, name]),
        where callable is exposed via XML-RPC if the authenticated user has the
        appropriate permission.
            
        The callable itself can be a method or a normal method. The first
        argument passed will always be a request object. The XMLRPCSystem
        performs some extra magic to remove the "self" and "req" arguments when
        listing the available methods.

        Signatures is a list of XML-RPC introspection signatures for this
        method. Each signature is a tuple consisting of the return type
        followed by argument types.
        """


class AbstractRPCHandler(Component):
    implements(IXMLRPCHandler)
    abstract = True

    def _init_methods(self):
        import inspect
        self._rpc_methods = []
        for name, val in inspect.getmembers(self):
            if hasattr(val, '_xmlrpc_signatures'):
                self._rpc_methods.append((val._xml_rpc_permission, val._xmlrpc_signatures, val, name))

    def xmlrpc_methods(self):
        if not hasattr(self, '_rpc_methods'):
            self._init_methods()
        return self._rpc_methods


class Method(object):
    """ Represents an XML-RPC exposed method. """
    def __init__(self, provider, permission, signatures, callable, name = None):
        """ Accept a signature in the form returned by xmlrpc_methods. """
        import pydoc
        self.permission = permission
        self.callable = callable
        self.rpc_signatures = signatures
        self.description = pydoc.getdoc(callable)
        if name is None:
            self.name = provider.xmlrpc_namespace() + '.' + callable.__name__
        else:
            self.name = provider.xmlrpc_namespace() + '.' + name
        self.namespace = provider.xmlrpc_namespace()
        self.namespace_description = pydoc.getdoc(provider)

    def __call__(self, req, args):
        req.perm.assert_permission(self.permission)
        result = self.callable(req, *args)
        # If result is null, return a zero
        if result is None:
            result = 0
        elif isinstance(result, dict):
            pass
        elif not isinstance(result, basestring):
            # Try and convert result to a list
            try:
                result = [i for i in result]
            except TypeError:
                pass
        return (result,)

    def _get_signature(self):
        """ Return the signature of this method. """
        if hasattr(self, '_signature'):
            return self._signature
        fullargspec = inspect.getargspec(self.callable)
        argspec = fullargspec[0]
        assert argspec[0:2] == ['self', 'req'] or argspec[0] == 'req', \
            'Invalid argspec %s for %s' % (argspec, self.name)
        while argspec and (argspec[0] in ('self', 'req')):
            argspec.pop(0)
        argspec.reverse()
        defaults = fullargspec[3]
        if not defaults:
            defaults = []
        else:
            defaults = list(defaults)
        args = []
        sig = []
        for sigcand in self.xmlrpc_signatures():
            if len(sig) < len(sigcand):
                sig = sigcand
        sig = list(sig)
        for arg in argspec:
            if defaults:
                value = defaults.pop()
                if type(value) is str:
                    if '"' in value:
                        value = "'%s'" % value
                    else:
                        value = '"%s"' % value
                arg += '=%s' % value
            args.insert(0, RPC_TYPES[sig.pop()] + ' ' + arg)
        self._signature = '%s %s(%s)' % (RPC_TYPES[sig.pop()], self.name, ', '.join(args))
        return self._signature

    signature = property(_get_signature)

    def xmlrpc_signatures(self):
        """ Signature as an XML-RPC 'signature'. """
        return self.rpc_signatures


class XMLRPCSystem(Component):
    """ Core of the XML-RPC system. """
    implements(IPermissionRequestor, IXMLRPCHandler)

    method_handlers = ExtensionPoint(IXMLRPCHandler)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'XML_RPC'

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'system'

    def xmlrpc_methods(self):
        yield ('XML_RPC', ((list, list),), self.multicall)
        yield ('XML_RPC', ((list,),), self.listMethods)
        yield ('XML_RPC', ((str, str),), self.methodHelp)
        yield ('XML_RPC', ((list, str),), self.methodSignature)
        yield ('XML_RPC', ((list,),), self.getAPIVersion)

    def get_method(self, method):
        """ Get an RPC signature by full name. """ 
        for provider in self.method_handlers:
            for candidate in provider.xmlrpc_methods():
                #self.env.log.debug(candidate)
                p = Method(provider, *candidate)
                if p.name == method:
                    return p
        raise xmlrpclib.Fault(1, 'XML-RPC method "%s" not found' % method)
        
    # Exported methods
    def all_methods(self, req):
        """ List all methods exposed via XML-RPC. Returns a list of Method objects. """
        for provider in self.method_handlers:
            for candidate in provider.xmlrpc_methods():
                # Expand all fields of method description
                c = Method(provider, *candidate)
                if req.perm.has_permission(c.permission):
                    yield c

    def multicall(self, req, signatures):
        """ Takes an array of XML-RPC calls encoded as structs of the form (in
        a Pythonish notation here):

        {'methodName': string, 'params': array}
        """
        for signature in signatures:
            try:
                yield self.get_method(signature['methodName'])(req, signature['params'])
            except xmlrpclib.Fault, e:
                yield e
            except Exception, e:
                yield xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), signature['methodName']))

    def listMethods(self, req):
        """ This method returns a list of strings, one for each (non-system)
        method supported by the XML-RPC server. """
        for method in self.all_methods(req):
            yield method.name

    def methodHelp(self, req, method):
        """ This method takes one parameter, the name of a method implemented
        by the XML-RPC server. It returns a documentation string describing the
        use of that method. If no such string is available, an empty string is
        returned. The documentation string may contain HTML markup. """
        p = self.get_method(method)
        req.perm.assert_permission(p.permission)
        return '\n'.join((p.signature, '', p.description))

    def methodSignature(self, req, method):
        """ This method takes one parameter, the name of a method implemented
        by the XML-RPC server.

        It returns an array of possible signatures for this method. A signature
        is an array of types. The first of these types is the return type of
        the method, the rest are parameters. """
        p = self.get_method(method)
        req.perm.assert_permission(p.permission)
        return [','.join([RPC_TYPES[x] for x in sig]) for sig in p.xmlrpc_signatures()]

    def getAPIVersion(self, req):
        """ Returns a list with two elements. First element is the major
        version number, second is the minor. Changes to the major version
        indicate API breaking changes, while minor version changes are simple
        additions, bug fixes, etc. """
        return [0, 2]
