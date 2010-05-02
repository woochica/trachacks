# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import inspect
import types
from datetime import datetime
import xmlrpclib

from trac.core import *
from trac.perm import IPermissionRequestor

__all__ = ['expose_rpc', 'IRPCProtocol', 'IXMLRPCHandler', 'AbstractRPCHandler',
            'Method', 'XMLRPCSystem', 'Binary', 'RPCError', 'MethodNotFound', 
            'ProtocolException', 'ServiceException']

class Binary(xmlrpclib.Binary):
    """ RPC Binary type. Currently == xmlrpclib.Binary. """
    pass

#----------------------------------------------------------------
# RPC Exception classes
#----------------------------------------------------------------
class RPCError(TracError):
    """ Error class for general RPC-related errors. """

class MethodNotFound(RPCError):
    """ Error to raise when requested method is not found. """

class _CompositeRpcError(RPCError):
    def __init__(self, details, title=None, show_traceback=False):
        if isinstance(details, Exception):
          self._exc = details
          message = unicode(details)
        else :
          self._exc = None
          message = details
        RPCError.__init__(self, message, title, show_traceback)
    def __unicode__(self):
        return u"%s details : %s" % (self.__class__.__name__, self.message)

class ProtocolException(_CompositeRpcError):
    """Protocol could not handle RPC request. Usually this means 
    that the request has some sort of syntactic error, a library 
    needed to parse the RPC call is not available, or similar errors."""

class ServiceException(_CompositeRpcError):
    """The called method threw an exception. Helpful to identify bugs ;o)"""

RPC_TYPES = {int: 'int', bool: 'boolean', str: 'string', float: 'double',
             datetime: 'dateTime.iso8601', Binary: 'base64',
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


class IRPCProtocol(Interface):
    
    def rpc_info():
        """ Returns a tuple of (name, docs). Method provides
        general information about the protocol used for the RPC HTML view.
        
        name: Shortname like 'XML-RPC'.
        docs: Documentation for the protocol.
        """

    def rpc_match():
        """ Return an iterable of (path_item, content_type) combinations that
        will be handled by the protocol.
        
        path_item: Single word to use for matching against
                   (/login)?/<path_item>. Answer to 'rpc' only if possible.
        content_type: Starts-with check of 'Content-Type' request header. """

    def parse_rpc_request(req, content_type):
        """ Parse RPC requests. 
        
        req          :        HTTP request object
        content_type :        Input MIME type
        
        Return a dictionary with the following keys set. All the other 
        values included in this mapping will be ignored by the core 
        RPC subsystem, will be protocol-specific, and SHOULD NOT be 
        needed in order to invoke a given method.

        method  (MANDATORY): target method name (e.g. 'ticket.get')
        params  (OPTIONAL) : a tuple containing input positional arguments
        headers (OPTIONAL) : if the protocol supports custom headers set 
                              by the client, then this value SHOULD be a 
                              dictionary binding `header name` to `value`. 
                              However, protocol handlers as well as target 
                              RPC methods *MUST (SHOULD ?) NOT* rely on 
                              specific values assigned to a particular 
                              header in order to send a response back 
                              to the client.
        mimetype           : request MIME-type. This value will be set
                              by core RPC components after calling
                              this method so, please, ignore

        If the request cannot be parsed this method *MUST* raise 
        an instance of `ProtocolException` optionally wrapping another 
        exception containing details about the failure.
        """

    def send_rpc_result(req, result):
        """Serialize the result of the RPC call and send it back to 
        the client.
        
        req     : Request object. The same mapping returned by 
                  `parse_rpc_request` can be accessed through 
                  `req.rpc` (see above).
        result  : The value returned by the target RPC method
        """

    def send_rpc_error(req, rpcreq, e):
        """Send a fault message back to the caller. Exception type 
        and message are used for this purpose. This method *SHOULD* 
        handle `RPCError`, `PermissionError`, `ResourceNotFound` and 
        their subclasses. This method is *ALWAYS* called from within 
        an exception handler.
        
        req     : Request object. The same mapping returned by 
                  `parse_rpc_request` can be accessed through 
                  `req.rpc` (see above).
        e       : exception object describing the failure
        """

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
        self.permission = permission
        self.callable = callable
        self.rpc_signatures = signatures
        self.description = inspect.getdoc(callable)
        if name is None:
            self.name = provider.xmlrpc_namespace() + '.' + callable.__name__
        else:
            self.name = provider.xmlrpc_namespace() + '.' + name
        self.namespace = provider.xmlrpc_namespace()
        self.namespace_description = inspect.getdoc(provider)

    def __call__(self, req, args):
        if self.permission:
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
    """ Core of the RPC system. """
    implements(IPermissionRequestor, IXMLRPCHandler)

    method_handlers = ExtensionPoint(IXMLRPCHandler)

    def __init__(self):
        self.env.systeminfo.append(('RPC',
                        __import__('tracrpc', ['__version__']).__version__))

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
        raise MethodNotFound('RPC method "%s" not found' % method)
        
    # Exported methods
    def all_methods(self, req):
        """ List all methods exposed via RPC. Returns a list of Method objects. """
        for provider in self.method_handlers:
            for candidate in provider.xmlrpc_methods():
                # Expand all fields of method description
                yield Method(provider, *candidate)

    def multicall(self, req, signatures):
        """ Takes an array of RPC calls encoded as structs of the form (in
        a Pythonish notation here): `{'methodName': string, 'params': array}`.
        For JSON-RPC multicall, signatures is an array of regular method call
        structs, and result is an array of return structures.
        """
        for signature in signatures:
            try:
                yield self.get_method(signature['methodName'])(req, signature['params'])
            except Exception, e:
                yield e

    def listMethods(self, req):
        """ This method returns a list of strings, one for each (non-system)
        method supported by the RPC server. """
        for method in self.all_methods(req):
            yield method.name

    def methodHelp(self, req, method):
        """ This method takes one parameter, the name of a method implemented
        by the RPC server. It returns a documentation string describing the
        use of that method. If no such string is available, an empty string is
        returned. The documentation string may contain HTML markup. """
        p = self.get_method(method)
        return '\n'.join((p.signature, '', p.description))

    def methodSignature(self, req, method):
        """ This method takes one parameter, the name of a method implemented
        by the RPC server.

        It returns an array of possible signatures for this method. A signature
        is an array of types. The first of these types is the return type of
        the method, the rest are parameters. """
        p = self.get_method(method)
        return [','.join([RPC_TYPES[x] for x in sig]) for sig in p.xmlrpc_signatures()]

    def getAPIVersion(self, req):
        """ Returns a list with three elements. First element is the
        epoch (0=Trac 0.10, 1=Trac 0.11 or higher). Second element is the major
        version number, third is the minor. Changes to the major version
        indicate API breaking changes, while minor version changes are simple
        additions, bug fixes, etc. """
        import tracrpc
        return map(int, tracrpc.__version__.split('-')[0].split('.'))
