# -*- coding: utf-8 -*-
# 
# Date:         Mon Jun 22 12:39:48 MDT 2009
# Copyright:    2009 CodeRage
# Author:       Jonathan Turkanis
# 
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

import re
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html

class AccessMacro(Component):
    """
    Apply access control to part of a wiki page.

    Example:

    {{{
    This is seen by everyone

    {{{
    #!access
    #allow(TICKET_ADMIN, MILESTONE_ADMIN)

    This is seen only by users with one of the permissions TICKET_ADMIN or MILESTONE_ADMIN
    }}}

    {{{
    #!access
    #deny(REPORT_VIEW)

    This is seen only by users who do not have the REPORT_VIEW permission
    }}}

    [[access(deny(REPORT_VIEW), This is an alternate syntax)]]

    }}}
    """
    implements(IWikiMacroProvider)

    PARSE_RULE = re.compile(r'^\s*(allow|deny)\s*\(\s*([^,)]+\s*(?:,\s*[^,\)]+)*)\)(.*)', re.I)
    SPLIT_LIST = re.compile(r'\s*,\s*')

    # IWikiMacroProvider
    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        return ["access"]

    # IWikiMacroProvider
    def get_macro_description(self, name):
        return "A Trac macro to display or hide parts of wiki pages based on permissions."

    # IWikiMacroProvider
    def expand_macro(self, formatter, name, content):
        """Called by the formatter when rendering the parsed wiki text."""

        # Parse access rule
        action = permissions = body = lines = None
        multiline = content.find("\n") != -1
        if multiline:
            lines = content.split("\n")
            if not lines[0] or lines[0][0] != '#':
                raise TracError('Missing permission specification')
            match = self.PARSE_RULE.match(lines[0][1:])
            if match:
                action = match.group(1)
                permissions = self.SPLIT_LIST.split(match.group(2).strip())
            else:
                raise TracError("Invalid permission specification: %s" % lines[0][1:])
        else:
            match = self.PARSE_RULE.match(content)
            if match:
                action = match.group(1)
                permissions = self.SPLIT_LIST.split(match.group(2).strip())
                body = match.group(3).lstrip()
                if not body or body[0] != ',':
                    raise TracError("Invalid permission specification: %s" % content)
                body = body[1:]
            else:
                raise TracError("Invalid permission specification: %s" % content)

        # Check access
        allow = None
        if action.lower() == "allow":
            allow = False
            for p in permissions:
                if p in formatter.req.perm:
                    allow = True
                    break
        else:
            allow = True
            for p in permissions:
                if p in formatter.req.perm:
                    allow = False
                    break

        # Process text
        if not allow:
            return ''
        elif multiline:
            return format_to_html(self.env, formatter.context, "\n".join(lines[1:]))
        else:
            return body
    
