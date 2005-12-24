from trac.core import *
from trac.perm import IPermissionRequestor
import inspect
import types
import xmlrpclib

class IXMLRPCHandler(Interface):
    def xmlrpc_namespace():
        """ Return the namespace in which a set of functions lives. This is
            overridden if the 'name' element is provided by xmlrpc_procedures(). 
            
            If this method is not present the methods __module__ name will be
            used."""

    def xmlrpc_procedures():
        """ Return an iterator of (permission, callable[, name[, description]]),
            where callable is exposed via XML-RPC if the authenticated user has
            the appropriate permission.
            
            'name' is only necessary if callable.__name__ is not useful,
            typically with lambda functions. If it is not provided, the name of
            the function will be __module__.__name__.
            
            Similarly, 'description' is obtained from the callables docstring
            and is only necessary if this is not obtainable, again usually only
            with lambda functions.

            The callable itself can be a method or a normal function. The
            XMLRPCSystem performs some extra magic to remove the "self"
            argument when listing the available functions.
            """

class Procedure(object):
    def __init__(self, provider, signature):
        """ Accept a signature in the form returned by xmlrpc_procedures. """
        namespace = hasattr(provider, 'xmlrpc_namespace') and provider.xmlrpc_namespace() or None
        signature = list(signature)
        if len(signature) == 2:
            signature.append((namespace and namespace or signature[1].__module__) + '.' + signature[1].__name__)
        if len(signature) == 3:
            import pydoc
            signature.append(pydoc.getdoc(signature[1]))
        self.permission, self.callable, self.name, self.description = signature

    def __call__(self, req, args):
        req.perm.assert_permission(self.permission)
        # Pass optional "req" arg if required
        argspec = inspect.getargspec(self.callable)[0]
        if (argspec and argspec[0] == 'req') or (len(argspec) > 1 and argspec[0:2] == ['self', 'req']):
            result = self.callable(req, *args)
        else:
            result = self.callable(*args)
        # If result is null, return an empty tuple
        if result is None:
            result = tuple()
        # We'll fully traverse the generator results and return it as a tuple
        elif type(result) is types.GeneratorType:
            result = tuple(result)
        return (result,)

    def _get_signature(self):
        """ Return the function signature of this procedure. """
        if hasattr(self, '_signature'):
            return self._signature
        fullargspec = inspect.getargspec(self.callable)
        argspec = fullargspec[0]
        while argspec and (argspec[0] in ('self', 'req')):
            argspec.pop(0)
        argspec.reverse()
        defaults = fullargspec[3]
        if not defaults:
            defaults = []
        else:
            defaults = list(defaults)
        args = []
        for arg in argspec:
            if defaults:
                value = defaults.pop()
                if type(value) is str:
                    if '"' in value:
                        value = "'%s'" % value
                    else:
                        value = '"%s"' % value
                arg += '=%s' % value
            args.insert(0, arg)
        self._signature = '%s(%s)' % (self.name, ', '.join(args))
        return self._signature

    signature = property(_get_signature)

class XMLRPCSystem(Component):
    """ Core of the XML-RPC system. """
    implements(IXMLRPCHandler, IPermissionRequestor)

    procedures = ExtensionPoint(IXMLRPCHandler)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'XML_RPC'

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'system'

    def xmlrpc_procedures(self):
        yield ('XML_RPC', self.listMethodsDetailed)
        yield ('XML_RPC', self.multicall)
        yield ('XML_RPC', self.listMethods)
        yield ('XML_RPC', self.methodHelp)

    def get_procedure(self, procedure):
        """ Get an RPC signature by full name. """ 
        for provider in self.procedures:
            for candidate in provider.xmlrpc_procedures():
                p = Procedure(provider, candidate)
                if p.name == procedure:
                    return p
        raise xmlrpclib.Fault(1, 'XML-RPC procedure "%s" not found' % procedure)
        
    # Exported methods
    def listMethodsDetailed(self, req):
        """ List all functions exposed via XML-RPC. Returns a list of tuples in
            the form (function_signature, description, permission). """
        for provider in self.procedures:
            for candidate in provider.xmlrpc_procedures():
                # Expand all fields of function description
                c = Procedure(provider, candidate)
                if not req.perm.has_permission(c.permission):
                    continue
                yield (c.signature, c.description, c.permission)

    def multicall(self, req, signatures):
        """ Takes an array of XML-RPC calls encoded as structs of the form (in
            a Pythonish notation here):

            {'methodName': string, 'params': array}
        """
        for signature in signatures:
            try:
                yield self.get_procedure(signature['methodName'])(req, signature['params'])
            except xmlrpclib.Fault, e:
                yield e
            except Exception, e:
                yield xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), signature['methodName']))

    def listMethods(self):
        """ This method returns a list of strings, one for each (non-system)
        method supported by the XML-RPC server. """
        for provider in self.procedures:
            for candidate in provider.xmlrpc_procedures():
                yield Procedure(provider, candidate).name

    def methodHelp(self, procedure):
        """ This method takes one parameter, the name of a method implemented
        by the XML-RPC server. It returns a documentation string describing the
        use of that method. If no such string is available, an empty string is
        returned. The documentation string may contain HTML markup. """
        p = self.get_procedure(procedure)
        return '\n'.join((p.signature, '', p.description))
