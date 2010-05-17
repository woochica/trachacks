# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import datetime
from itertools import izip
import re
from types import GeneratorType

from trac.core import *
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.datefmt import utc
from trac.util.text import to_unicode
from trac.web.api import RequestDone

from tracrpc.api import IRPCProtocol, XMLRPCSystem, Binary, \
        RPCError, MethodNotFound, ProtocolException
from tracrpc.util import exception_to_unicode, empty, prepare_docs

__all__ = ['JsonRpcProtocol']

try:
    import json
    if not (hasattr(json, 'JSONEncoder') \
            and hasattr(json, 'JSONDecoder')):
        raise AttributeError("Incorrect JSON library found.")
except (ImportError, AttributeError):
    try:
        import simplejson as json
    except ImportError:
        json = None
        __all__ = []

if json:
    class TracRpcJSONEncoder(json.JSONEncoder):
        """ Extending the JSON encoder to support some additional types:
        1. datetime.datetime => {'__jsonclass__': ["datetime", "<rfc3339str>"]}
        2. tracrpc.api.Binary => {'__jsonclass__': ["binary", "<base64str>"]}
        3. empty => '' """

        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                # http://www.ietf.org/rfc/rfc3339.txt
                return {'__jsonclass__': ["datetime",
                                obj.strftime('%Y-%m-%dT%H:%M:%S')]}
            elif isinstance(obj, Binary):
                return {'__jsonclass__': ["binary",
                                obj.data.encode("base64")]}
            elif obj is empty:
                return ''
            else:
                return json.JSONEncoder(self, obj)

    class TracRpcJSONDecoder(json.JSONDecoder):
        """ Extending the JSON decoder to support some additional types:
        1. {'__jsonclass__': ["datetime", "<rfc3339str>"]} => datetime.datetime
        2. {'__jsonclass__': ["binary", "<base64str>"]} => tracrpc.api.Binary """

        dt = re.compile(
            '^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,}))?')

        def _normalize(self, obj):
            """ Helper to traverse JSON decoded object for custom types. """
            if isinstance(obj, tuple):
                return tuple(self._normalize(item) for item in obj)
            elif isinstance(obj, list):
                return [self._normalize(item) for item in obj]
            elif isinstance(obj, dict):
                if obj.keys() == ['__jsonclass__']:
                    kind, val = obj['__jsonclass__']
                    if kind == 'datetime':
                        dt = self.dt.match(val)
                        if not dt:
                            raise Exception(
                                    "Invalid datetime string (%s)" % val)
                        dt = tuple([int(i) for i in dt.groups() if i])
                        kw_args = {'tzinfo': utc}
                        return datetime.datetime(*dt, **kw_args)
                    elif kind == 'binary':
                        try:
                            bin = val.decode("base64")
                            return Binary(bin)
                        except:
                            raise Exception("Invalid base64 string")
                    else:
                        raise Exception("Unknown __jsonclass__: %s" % kind)
                else:
                    return dict(self._normalize(obj.items()))
            elif isinstance(obj, basestring):
                return to_unicode(obj)
            else:
                return obj

        def decode(self, obj, *args, **kwargs):
            obj = json.JSONDecoder.decode(self, obj, *args, **kwargs)
            return self._normalize(obj)

    class JsonProtocolException(ProtocolException):
        """Impossible to handle JSON-RPC request."""
        def __init__(self, details, code=-32603, title=None, show_traceback=False):
            ProtocolException.__init__(self, details, title, show_traceback)
            self.code = code

    class JsonRpcProtocol(Component):
        r"""
        Example `POST` request using `curl` with `Content-Type` header
        and body:
 
        {{{
        user: ~ > cat body.json
        {"params": ["WikiStart"], "method": "wiki.getPage", "id": 123}
        user: ~ > curl -H "Content-Type: application/json" --data @body.json ${req.abs_href.rpc()}
        {"id": 123, "error": null, "result": "= Welcome to....
        }}}
    
        Implementation details:
    
          * JSON-RPC has no formalized type system, so a class-hint system is used
            for input and output of non-standard types:
            * `{"__jsonclass__": ["datetime", "YYYY-MM-DDTHH:MM:SS"]} => DateTime (UTC)`
            * `{"__jsonclass__": ["binary", "<base64-encoded>"]} => Binary`
          * `"id"` is optional, and any marker value received with a
            request is returned with the response.
        """

        implements(IRPCProtocol)

        # IRPCProtocol methods

        def rpc_info(self):
            return ('JSON-RPC', prepare_docs(self.__doc__))

        def rpc_match(self):
            yield('rpc', 'application/json')
            # Legacy path - provided for backwards compatibility:
            yield ('jsonrpc', 'application/json')

        def parse_rpc_request(self, req, content_type):
            """ Parse JSON-RPC requests"""
            if not json:
                self.log.debug("RPC(json) call ignored (not available).")
                raise JsonProtocolException("Error: JSON-RPC not available.\n")
            try:
                data = json.load(req, cls=TracRpcJSONDecoder)
                self.log.info("RPC(json) JSON-RPC request ID : %s.", data.get('id'))
                if data.get('method') == 'system.multicall':
                    # Prepare for multicall
                    self.log.debug("RPC(json) Multicall request %s", data)
                    params = data.get('params', [])
                    for signature in params :
                        signature['methodName'] = signature.get('method', '')
                    data['params'] = [params]
                return data
            except Exception, e:
                # Abort with exception - no data can be read
                self.log.error("RPC(json) decode error %s", 
                                  exception_to_unicode(e, traceback=True))
                raise JsonProtocolException(e, -32700)

        def send_rpc_result(self, req, result):
            """Send JSON-RPC response back to the caller."""
            rpcreq = req.rpc
            r_id = rpcreq.get('id')
            try:
                if rpcreq.get('method') == 'system.multicall': 
                    # Custom multicall
                    args = (rpcreq.get('params') or [[]])[0]
                    mcresults = [self._json_result(
                                            isinstance(value, Exception) and \
                                                        value or value[0], \
                                            sig.get('id') or r_id) \
                                  for sig, value in izip(args, result)]
                
                    response = self._json_result(mcresults, r_id)
                else:
                    response = self._json_result(result, r_id)
                try: # JSON encoding
                    self.log.debug("RPC(json) result: %s" % repr(response))
                    response = json.dumps(response, cls=TracRpcJSONEncoder)
                except Exception, e:
                    response = json.dumps(self._json_error(e, r_id=r_id),
                                            cls=TracRpcJSONEncoder)
            except Exception, e:
                self.log.error("RPC(json) error %s" % exception_to_unicode(e,
                                                        traceback=True))
                response = json.dumps(self._json_error(e, r_id=r_id),
                                cls=TracRpcJSONEncoder)
            self._send_response(req, response + '\n', rpcreq['mimetype'])

        def send_rpc_error(self, req, e):
            """Send a JSON-RPC fault message back to the caller. """
            rpcreq = req.rpc
            r_id = rpcreq.get('id')
            response = json.dumps(self._json_error(e, r_id=r_id), \
                                      cls=TracRpcJSONEncoder)
            self._send_response(req, response + '\n', rpcreq['mimetype'])

        # Internal methods

        def _send_response(self, req, response, content_type='application/json'):
            self.log.debug("RPC(json) encoded response: %s" % response)
            response = to_unicode(response).encode("utf-8")
            req.send_response(200)
            req.send_header('Content-Type', content_type)
            req.send_header('Content-Length', len(response))
            req.end_headers()
            req.write(response)
            raise RequestDone()

        def _json_result(self, result, r_id=None):
            """ Create JSON-RPC response dictionary. """
            if not isinstance(result, Exception):
                return {'result': result, 'error': None, 'id': r_id}
            else :
                return self._json_error(result, r_id=r_id)

        def _json_error(self, e, c=None, r_id=None):
            """ Makes a response dictionary that is an error. """
            if isinstance(e, MethodNotFound):
                c = -32601
            elif isinstance(e, PermissionError):
                c = 403
            elif isinstance(e, ResourceNotFound):
                c = 404
            else:
                c = c or hasattr(e, 'code') and e.code or -32603
            return {'result': None, 'id': r_id, 'error': {
                    'name': hasattr(e, 'name') and e.name or 'JSONRPCError',
                    'code': c,
                    'message': to_unicode(e)}}

