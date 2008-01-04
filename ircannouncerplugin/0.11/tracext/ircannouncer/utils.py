# -*- coding: utf-8 -*-
"""
    ircannouncer.utils
    ~~~~~~~~~~~~~~~~~~

    Contains some utils.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import posixpath
from SimpleXMLRPCServer import CGIXMLRPCRequestHandler, Fault

from trac.core import TracError


class TracXMLRPCRequestHandler(CGIXMLRPCRequestHandler):
    """Simple XMLRPC handler for trac."""

    def __init__(self, methods):
        CGIXMLRPCRequestHandler.__init__(self)
        self.methods = methods

    def dispatch(self, req):
        try:
            data = req.read(int(req.get_header('Content-Length')))
        except (TypeError, ValueError):
            raise TracError('This is an XMLRPC entrypoint.')
        response = self._marshaled_dispatch(data, lambda method, args:
                                            self.methods[method](req, *args))

        req.send_response(200)
        req.send_header('Content-Type', 'application/xml')
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)


def NotFound(msg='Not Found'):
    """Factory function that generates a fault code for missing resources"""
    return Fault(50, msg)


def add_environment_info(env, values):
    """Add infos about the trac to the values dict."""
    url = env.abs_href()
    if not url.endswith('/'):
        url += '/'
    values['trac'] = {
        'name':         env.project_name,
        'description':  env.project_description,
        'url':          url
    }
    return values


def prepare_ticket_values(ticket, action=None):
    """Converts a ticket object into a dict."""
    values = ticket.values.copy()
    values['id'] = ticket.id
    if action is not None:
        values['action'] = action
    values['url'] = ticket.env.abs_href.ticket(ticket.id)
    return add_environment_info(ticket.env, values)


def prepare_changeset_values(env, chgset):
    """Converts a changeset object into a dict."""
    outer_path = None
    files = 0
    for path, kind, change, base_path, base_rev in chgset.get_changes():
        directory = posixpath.dirname(path)
        if outer_path is None:
            outer_path = directory
        else:
            outer_path = posixpath.commonprefix((outer_path, directory))
        files += 1
    if not outer_path.startswith('/'):
        outer_path = '/' + outer_path
    return add_environment_info(env, {
        'file_count':   files,
        'path':         outer_path,
        'rev':          chgset.rev,
        'author':       chgset.author,
        'message':      chgset.message,
        'url':          env.abs_href.changeset(chgset.rev)
    })


def prepare_wiki_page_values(page, action=None):
    """Converts a wiki page object into a dict."""
    values = add_environment_info(page.env, {
        'name':         page.name,
        'version':      page.version,
        'readonly':     page.readonly,
        'exists':       page.exists,
        'author':       page.author or '',
        'comment':      page.comment or '',
        'url':          page.env.abs_href.wiki(page.name)
    })
    if action is not None:
        values['action'] = action
    return values
