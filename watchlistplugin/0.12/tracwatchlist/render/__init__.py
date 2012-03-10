# -*- coding: utf-8 -*-
"""
 This file is part of the Watchlist Plugin for Trac.
 Copyright (c) 2008-2010  Martin Scharrer <martin@scharrer-online.de>

 IMPORTANT NOTE:
 Code taken and minimal modified from
 trac.ticket.web_ui.TicketModule._render_property_diff
 (from both Trac 0.11.7 and 0.12) which is licensed under the
 modified BSD license:

    Copyright (C) 2003-2009 Edgewall Software
    Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
    Author: Jonas Borgström <jonas@edgewall.com>
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
    3. The name of the author may not be used to endorse or promote
    products derived from this software without specific prior
    written permission.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
    OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
    GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
    WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 Notable changes:
    * Converted to stand-alone function which can be called by plug-ins
    * Added Trac version check to use one definition for Trac 0.11 and
      another for Trac 0.12.
    * Added special format for attachments

 The contribution of Martin Scharrer is licenced under the modified BSD licence
 (see above) and the the GPL (v3 or later) licence. Either licence can be used for
 derivatives.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    For a copy of the GNU General Public License see
    <http://www.gnu.org/licenses/>.

 i18n notice:
 This file uses the same domain as trac itself, not the one for the WatchlistPlugin.

 $Id$
"""

from  trac.core              import  *
from  trac.resource          import  get_resource_url
from  trac.web.chrome        import  Chrome
from  genshi.builder         import  tag
from  trac.util.presentation import  separated
from  trac.util.text         import  obfuscate_email_address
from  trac.util.translation  import  _
from  tracwatchlist.translation  import  tag_ as wtag_

try:
    from  trac.util.translation  import  tag_, tagn_

    def render_property_diff(env, req, ticket, field, old, new,
                              resource_new=None):
        "Version for Trac 0.12"
        rendered = None
        # per type special rendering of diffs
        type_ = None
        for f in ticket.fields:
            if f['name'] == field:
                type_ = f['type']
                break
        if type_ == 'checkbox':
            rendered = new == '1' and _("set") or _("unset")
        elif type_ == 'textarea':
            if not resource_new:
                rendered = _("modified")
            else:
                href = get_resource_url(env, resource_new, req.href,
                                        action='diff')
                # TRANSLATOR: modified ('diff') (link)
                diff = tag.a(_("diff"), href=href)
                rendered = tag_("modified (%(diff)s)", diff=diff)

        # per name special rendering of diffs
        old_list, new_list = None, None
        render_elt = lambda x: x
        sep = ', '
        if field == 'cc':
            chrome = Chrome(env)
            old_list, new_list = chrome.cc_list(old), chrome.cc_list(new)
            if not (Chrome(env).show_email_addresses or
                    'EMAIL_VIEW' in req.perm(resource_new or ticket.resource)):
                render_elt = obfuscate_email_address
        elif field == 'keywords':
            old_list, new_list = old.split(), new.split()
            sep = ' '
        if (old_list, new_list) != (None, None):
            added = [tag.em(render_elt(x)) for x in new_list
                     if x not in old_list]
            remvd = [tag.em(render_elt(x)) for x in old_list
                     if x not in new_list]
            added = added and tagn_("%(items)s added", "%(items)s added",
                                    len(added), items=separated(added, sep))
            remvd = remvd and tagn_("%(items)s removed", "%(items)s removed",
                                    len(remvd), items=separated(remvd, sep))
            if added or remvd:
                rendered = tag(added, added and remvd and _("; "), remvd)
                return rendered
        if field in ('reporter', 'owner'):
            if not (Chrome(env).show_email_addresses or
                    'EMAIL_VIEW' in req.perm(resource_new or ticket.resource)):
                old = obfuscate_email_address(old)
                new = obfuscate_email_address(new)
        # Added by MS
        # The `wtag_` is the `tag_` from tracwatchlist.translation, e.g. 
        # using its translation domain.
        if field == 'attachment':
            rendered = wtag_("%(value)s added", value=tag.em(new))
        # changed 'if' to 'elif':
        elif old and not new:
            rendered = tag_("%(value)s deleted", value=tag.em(old))
        elif new and not old:
            rendered = tag_("set to %(value)s", value=tag.em(new))
        elif old and new:
            rendered = tag_("changed from %(old)s to %(new)s",
                            old=tag.em(old), new=tag.em(new))
        return rendered

except ImportError:

    def render_property_diff(self, req, ticket, field, old, new,
                              resource_new=None):
        "Version for Trac 0.11"
        rendered = None
        # per type special rendering of diffs
        type_ = None
        for f in ticket.fields:
            if f['name'] == field:
                type_ = f['type']
                break
        if type_ == 'checkbox':
            rendered = new == '1' and "set" or "unset"
        elif type_ == 'textarea':
            if not resource_new:
                rendered = _('modified')
            else:
                href = get_resource_url(self.env, resource_new, req.href,
                                        action='diff')
                rendered = tag('modified (', tag.a('diff', href=href), ')')

        # per name special rendering of diffs
        old_list, new_list = None, None
        render_elt = lambda x: x
        sep = ', '
        if field == 'cc':
            chrome = Chrome(self.env)
            old_list, new_list = chrome.cc_list(old), chrome.cc_list(new)
            if not (Chrome(self.env).show_email_addresses or
                    'EMAIL_VIEW' in req.perm(resource_new or ticket.resource)):
                render_elt = obfuscate_email_address
        elif field == 'keywords':
            old_list, new_list = (old or '').split(), new.split()
            sep = ' '
        if (old_list, new_list) != (None, None):
            added = [tag.em(render_elt(x)) for x in new_list
                     if x not in old_list]
            remvd = [tag.em(render_elt(x)) for x in old_list
                     if x not in new_list]
            added = added and tag(separated(added, sep), " added")
            remvd = remvd and tag(separated(remvd, sep), " removed")
            if added or remvd:
                rendered = tag(added, added and remvd and '; ', remvd)
                return rendered
        if field in ('reporter', 'owner'):
            if not (Chrome(self.env).show_email_addresses or
                    'EMAIL_VIEW' in req.perm(resource_new or ticket.resource)):
                old = obfuscate_email_address(old)
                new = obfuscate_email_address(new)
        # Added by MS
        if field == 'attachment':
            rendered = tag(tag.em(new), " added")
        # changed 'if' to 'elif':
        elif old and not new:
            rendered = tag(tag.em(old), " deleted")
        elif new and not old:
            rendered = tag("set to ", tag.em(new))
        elif old and new:
            rendered = tag("changed from ", tag.em(old),
                            " to ", tag.em(new))
        return rendered

# EOF
