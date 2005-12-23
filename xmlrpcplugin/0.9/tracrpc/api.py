from trac.core import *
from trac.perm import IPermissionRequestor
import inspect

class IXMLRPCHandler(Interface):
    def get_xmlrpc_functions():
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

class XMLRPCSystem(Component):
    implements(IXMLRPCHandler, IPermissionRequestor)

    procedures = ExtensionPoint(IXMLRPCHandler)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'XML_RPC'

    # IXMLRPCHandler methods
    def get_xmlrpc_functions(self):
        yield ('TRAC_ADMIN', self.list_xmlrpc_functions)

    def list_xmlrpc_functions(self, req):
        """ List all functions exposed via XML-RPC. Returns a list of binary
        tuples where the first element is the function signature and the second
        element is the description. """
        out = []
        for provider in self.procedures:
            for candidate in provider.get_xmlrpc_functions():
                c = self.resolve_candidate(candidate)
                if not req.perm.has_permission(c[0]):
                    continue
                fullargspec = inspect.getargspec(c[1])
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
                out.append(('%s(%s)' % (c[2], ', '.join(args)), c[3].strip()))
        return out

    def resolve_candidate(self, candidate):
        """ Expand function signature returned by get_xmlrpc_functions() so
            that all four fields have something useful in them. """
        candidate = list(candidate)
        if len(candidate) == 2:
            candidate.append(candidate[1].__module__ + '.' + candidate[1].__name__)
        if len(candidate) == 3:
            import pydoc
            candidate.append(pydoc.getdoc(candidate[1]))
        return candidate
