# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import datetime
import time
import xmlrpclib

import genshi

from trac.core import *
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.datefmt import utc
from trac.util.text import to_unicode
from trac.web.api import RequestDone

from tracrpc.api import XMLRPCSystem, IRPCProtocol, Binary, \
        RPCError, MethodNotFound, ProtocolException, ServiceException
from tracrpc.util import empty, prepare_docs

__all__ = ['XmlRpcProtocol']

def to_xmlrpc_datetime(dt):
    """ Convert a datetime.datetime object to a xmlrpclib DateTime object """
    return xmlrpclib.DateTime(dt.utctimetuple())

def from_xmlrpc_datetime(data):
    """Return datetime (in utc) from XMLRPC datetime string (is always utc)"""
    t = list(time.strptime(data.value, "%Y%m%dT%H:%M:%S")[0:6])
    return apply(datetime.datetime, t, {'tzinfo': utc})

class XmlRpcProtocol(Component):
    r"""
    There should be XML-RPC client implementations available for all
    popular programming languages.
    Example call using `curl`:

    {{{
    user: ~ > cat body.xml
    <?xml version="1.0"?>
    <methodCall>
    <methodName>wiki.getPage</methodName>
    <params>
    <param><string>WikiStart</string></param>
    </params>
    </methodCall>
    
    user: ~ > curl -H "Content-Type: application/xml" --data @body.xml ${req.abs_href.rpc()}
    <?xml version='1.0'?>
    <methodResponse>
    <params>
    <param>
    <value><string>= Welcome to....
    }}}
    
    The following snippet illustrates how to perform authenticated calls in Python.
    
    {{{
    >>> from xmlrpclib import ServerProxy
    >>> p = ServerProxy('${req.abs_href.login('rpc').replace('://', '://%s:your_password@' % authname)}')
    >>> p.system.getAPIVersion()
    [${', '.join(rpc.version.split('.'))}]
    }}}
    """

    implements(IRPCProtocol)

    # IRPCProtocol methods

    def rpc_info(self):
        return ('XML-RPC', prepare_docs(self.__doc__))

    def rpc_match(self):
        # Legacy path xmlrpc provided for backwards compatibility:
        # Using this order to get better docs 
        yield ('rpc', 'application/xml')
        yield ('xmlrpc', 'application/xml')
        yield ('rpc', 'text/xml')
        yield ('xmlrpc', 'text/xml')

    def parse_rpc_request(self, req, content_type):
        """ Parse XML-RPC requests."""
        try:
            args, method = xmlrpclib.loads(
                        req.read(int(req.get_header('Content-Length'))))
        except Exception, e:
            self.log.debug("RPC(xml) parse error: %s", to_unicode(e))
            raise ProtocolException(xmlrpclib.Fault(-32700, to_unicode(e)))
        else :
            self.log.debug("RPC(xml) call by '%s', method '%s' with args: %s" \
                                        % (req.authname, method, repr(args)))
            args = self._normalize_xml_input(args)
            return {'method' : method, 'params' : args}

    def send_rpc_result(self, req, result):
        """Send the result of the XML-RPC call back to the client."""
        rpcreq = req.rpc
        method = rpcreq.get('method')
        self.log.debug("RPC(xml) '%s' result: %s" % (
                                                    method, repr(result)))
        result = tuple(self._normalize_xml_output([result]))
        self._send_response(req,
                xmlrpclib.dumps(result, methodresponse=True), rpcreq['mimetype'])

    def send_rpc_error(self, req, e):
        """Send an XML-RPC fault message back to the caller"""
        rpcreq = req.rpc
        fault = None
        if isinstance(e, ProtocolException):
            fault = e._exc
        elif isinstance(e, ServiceException):
            e = e._exc
        elif isinstance(e, MethodNotFound):
            fault = xmlrpclib.Fault(-32601, to_unicode(e))
        elif isinstance(e, PermissionError):
            fault = xmlrpclib.Fault(403, to_unicode(e))
        elif isinstance(e, ResourceNotFound):
            fault = xmlrpclib.Fault(404, to_unicode(e))

        if fault is not None :
            self._send_response(req, xmlrpclib.dumps(fault), rpcreq['mimetype'])
        else :
            self.log.error(e)
            import traceback
            from tracrpc.util import StringIO
            out = StringIO()
            traceback.print_exc(file = out)
            self.log.error(out.getvalue())
            err_code = hasattr(e, 'code') and e.code or 1
            method = rpcreq.get('method')
            self._send_response(req,
                    xmlrpclib.dumps(
                        xmlrpclib.Fault(err_code,
                            "'%s' while executing '%s()'" % (str(e), method))))

    # Internal methods

    def _send_response(self, req, response, content_type='application/xml'):
        response = to_unicode(response).encode("utf-8")
        req.send_response(200)
        req.send_header('Content-Type', content_type)
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)
        raise RequestDone

    def _normalize_xml_input(self, args):
        """ Normalizes arguments (at any level - traversing dicts and lists):
        1. xmlrpc.DateTime is converted to Python datetime
        2. tracrpc.api.Binary => xmlrpclib.Binary
        2. String line-endings same as from web (`\n` => `\r\n`)
        """
        new_args = []
        for arg in args:
            # self.env.log.debug("arg %s, type %s" % (arg, type(arg)))
            if isinstance(arg, xmlrpclib.DateTime):
                new_args.append(from_xmlrpc_datetime(arg))
            elif isinstance(arg, xmlrpclib.Binary):
                arg.__class__ = Binary
                new_args.append(arg)
            elif isinstance(arg, basestring):
                new_args.append(arg.replace("\n", "\r\n"))
            elif isinstance(arg, dict):
                for key, val in arg.items():
                    arg[key], = self._normalize_xml_input([val])
                new_args.append(arg)
            elif isinstance(arg, (list, tuple)):
                new_args.append(self._normalize_xml_input(arg))
            else:
                new_args.append(arg)
        return new_args

    def _normalize_xml_output(self, result):
        """ Normalizes and converts output (traversing it):
        1. None => ''
        2. datetime => xmlrpclib.DateTime
        3. Binary => xmlrpclib.Binary
        4. genshi.builder.Fragment|genshi.core.Markup => unicode
        """
        new_result = []
        for res in result:
            if isinstance(res, datetime.datetime):
                new_result.append(to_xmlrpc_datetime(res))
            elif isinstance(res, Binary):
                res.__class__ = xmlrpclib.Binary
                new_result.append(res)
            elif res is None or res is empty:
                new_result.append('')
            elif isinstance(res, (genshi.builder.Fragment, \
                                  genshi.core.Markup)):
                new_result.append(to_unicode(res))
            elif isinstance(res, dict):
                for key, val in res.items():
                    res[key], = self._normalize_xml_output([val])
                new_result.append(res)
            elif isinstance(res, list) or isinstance(res, tuple):
                new_result.append(self._normalize_xml_output(res))
            else:
                new_result.append(res)
        return new_result
