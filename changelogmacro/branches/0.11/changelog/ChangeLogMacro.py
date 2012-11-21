#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Alec Thomas
# Copyright (C) 2010-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.util import format_datetime
from StringIO import StringIO

class ChangeLogMacro(WikiMacroBase):
    """ Provides the macro

    {{{
       [[ChangeLog(path[,limit[,rev]])]]
    }}}

    which dumps the change log for path of revision rev, back
    limit revisions. "rev" can be 0 for the latest revision.

    limit and rev may be keyword arguments
    """

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        args, kwargs = parse_args(content)
        args += [None, None]
        path, limit, rev = args[:3]
        limit = kwargs.pop('limit', limit)
        rev = kwargs.pop('rev', rev)

        if 'CHANGESET_VIEW' not in req.perm:
            return Markup('<i>Changelog not available</i>')

        repo = self.env.get_repository(req.authname)

        if rev is None:
            rev = repo.get_youngest_rev()
        rev = repo.normalize_rev(rev)
        path = repo.normalize_path(path)
        if limit is None:
            limit = 5
        else:
            limit = int(limit)
        node = repo.get_node(path, rev)
        out = StringIO()
        out.write('<div class="changelog">\n')
        for npath, nrev, nlog in node.get_history(limit):
            change = repo.get_changeset(nrev)
            datetime = format_datetime(change.date, '%Y/%m/%d %H:%M:%S', req.tz)
            out.write(wiki_to_html("'''[%s] by %s on %s'''\n\n%s" %
                (nrev, change.author, datetime, change.message),
                                   self.env, req));
        out.write('</div>\n')
        return out.getvalue()
