#
#   updater.py
#
#   Manages the updating of the database by AJAX call.
#

import re, sys
from trac.core import Component, ExtensionPoint, implements
from trac.web import IRequestHandler
from genshi.builder import tag
from db import IChecklistDBObserver

class BadRequest(Exception):
    __http_status__ = 400

class PermissionDenied(Exception):
    __http_status__ = 401

class ChecklistUpdaterComponent(Component):
    """
    Used as an AJAX request handler, updates the database with the information
    provided to .../checklist/update.  The information contained is:

    __context__ : The context string to use for the fields provided.
    __fields__ : The other fields to be processed.

    All other query items are the checklist items that are turned "on".  These
    are then applied to the database.  The following response codes are
    produced by this URL:

    200 "OK"
        Operation successful.

    400 Problem message
        Indicates the input query could not be processed.

    401 "User %s cannot set %s."
        User is not allowed to complete the transaction.

    500 Exception type: error message
        A Python exception was encountered.
    """

    implements(IRequestHandler)

    clobservers = ExtensionPoint(IChecklistDBObserver)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.endswith('/checklist/update')

    def process_request(self, req):
        try:
            self.log.debug('UPDATE ARGS: ' + str(req.args))
            args = dict(req.args)
            backpath = args.pop('__backpath__', None)
            context = args.pop('__context__', None)
            if context is None:
                raise BadRequest('__context__ is required')
            who = str(req.session.sid)
            fields = args.pop('__fields__', ())
            if isinstance(fields, basestring):
                fields = (fields,)
            updates =[]
            for name in set(fields):
                value = bool(args.get(name)) and 'on' or ''
                oldvalue = bool(args.get('old:' + name)) and 'on' or ''
                can_set = args.get('can-set:' + name) or args.get('can-set:*')
                can_get = args.get('can-get:' + name) or args.get('can-get:*')
                can_change = args.get('can-change:' + name) \
                    or args.get('can-change:*')
                if value != oldvalue:
                    if value:
                        perm = can_set or can_change
                    else:
                        perm = can_get or can_change
                    perm = str(perm)
                    if perm and not req.perm.has_permission(perm):
                        raise PermissionDenied(
                            'You must have %r to do this.' % perm)
                    updates.append((context, name, value, who))
                self.updateFields(updates)
        except Exception, e:
            code = getattr(e, '__http_status__', 500)
            msg = str(e)
            if code == 500:
                msg = e.__class__.__name__ + ': ' + msg
            self.log.debug('ERROR DURING UPDATE: ' + msg)
            req.send_response(code)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write(msg)
        else:
            if backpath:
                req.send_response(302)
                req.send_header('Content-Type', 'text/plain')
                req.send_header('Location', backpath)
            else:
                req.send_response(200)
                req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write('OK')

    def updateFields(self, updates):
        # Broadcast the updates.
        for observer in self.clobservers:
            observer.checklist_updateFields(updates)

