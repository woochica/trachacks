# -*- coding: utf-8 -*-
"""
 This file is part of the Watchlist Plugin for Trac.
 Copyright (c) 2008-2010  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 Code taken and minimal modified from trac.ticket.web_ui.TicketModule._render_property_diff
 which is licensed under the modified BSD license. 
     Copyright (C) 2003-2009 Edgewall Software
     Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
     Author: Jonas Borgström <jonas@edgewall.com>
     See http://trac.edgewall.org/wiki/TracLicense

 i18n notice:
 This file uses the same domain as trac itself, not the one for the WatchlistPlugin.
"""

from  trac.core              import  *
from  trac.util.translation  import  _, tag_, tagn_
from  trac.resource          import  get_resource_url
from  trac.web.chrome        import  Chrome
from  genshi.builder         import  tag
from  trac.util.presentation import  separated
from  trac.util.text         import  obfuscate_email_address

def render_property_diff(env, req, ticket, field, old, new, 
                              resource_new=None):
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
        if old and not new:
            rendered = tag_("%(value)s deleted", value=tag.em(old))
        elif new and not old:
            rendered = tag_("set to %(value)s", value=tag.em(new))
        elif old and new:
            rendered = tag_("changed from %(old)s to %(new)s",
                            old=tag.em(old), new=tag.em(new))
        return rendered

