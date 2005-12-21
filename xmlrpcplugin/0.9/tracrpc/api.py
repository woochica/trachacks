from trac.core import *
import inspect

class IXMLRPCProvider(Interface):
    def get_xmlrpc_functions():
        """ Return an iterator of (permission, callable[, name[, description]]) whose interface is
            exposed via XML-RPC. If the authenticated user has permission the
            function is callable.
            
            'name' is only necessary if the callable.__name__ is not useful,
            eg. a lambda function. If it is not provided, the name of the function
            will be __module__.__name__."""

class XMLRPCSystem(Component):
    implements(IXMLRPCProvider)

    procedures = ExtensionPoint(IXMLRPCProvider)

    def get_procedures(self, req, provider):
        """ Iterate over RPC procedures, applying permissions. """
        for candidate in provider.get_xmlrpc_functions():
            if req.perm.has_permission(candidate[0]):
                yield self.resolve_candidate(candidate)
            

    def list_xmlrpc_functions(self):
        """ List all functions exposed via XML-RPC. Returns a list of binary
        tuples where the first element is the function signature and the second
        element is the description. """
        out = []
        for provider in self.procedures:
            for candidate in provider.get_xmlrpc_functions():
                c = self.resolve_candidate(candidate)
                fullargspec = inspect.getargspec(c[1])
                argspec = fullargspec[0]
                if argspec and argspec[0] == 'self':
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
                            value = '"%s"' % value
                        arg += '=%s' % value
                    args.insert(0, arg)
                out.append(('%s(%s)' % (c[2], ', '.join(args)), c[3].strip()))
        return out

    # IXMLRPCProvider methods
    def get_xmlrpc_functions(self):
        yield ('TRAC_ADMIN', self.list_xmlrpc_functions)

    # Helper methods
    def resolve_candidate(self, candidate):
        """ Expand function signature returned by get_xmlrpc_functions() so
            that all four fields have something useful in them. """
        candidate = list(candidate)
        if len(candidate) == 2:
            candidate.append(candidate[1].__module__ + '.' + candidate[1].__name__)
        if len(candidate) == 3:
            candidate.append(candidate[1].__doc__ or "No description")
        return candidate
