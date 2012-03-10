# -*- coding: utf-8 -*-
"""
= Watchlist Plugin for Trac =
Plugin Website:  http://trac-hacks.org/wiki/WatchlistPlugin
Trac website:    http://trac.edgewall.org/

Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
All rights reserved.

The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.

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

$Id$
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  trac.core              import  *
from  genshi.builder         import  tag
from  trac.ticket.model      import  Ticket
from  trac.ticket.api        import  TicketSystem
from  trac.util.datefmt      import  pretty_timedelta, \
                                     datetime, utc, to_timestamp
from  trac.util.text         import  to_unicode, obfuscate_email_address
from  trac.wiki.formatter    import  format_to_oneliner
from  trac.mimeview.api      import  Context
from  trac.web.chrome        import  Chrome
from  trac.resource          import  Resource
from  trac.attachment        import  Attachment

from  trac.util.datefmt      import  format_datetime as trac_format_datetime

from  tracwatchlist.api      import  BasicWatchlist
from  tracwatchlist.translation import  add_domain, _, N_, T_, t_, tag_, ngettext
from  tracwatchlist.render   import  render_property_diff
from  tracwatchlist.util     import  moreless, format_datetime, LC_TIME,\
                                     decode_range_sql


class TicketWatchlist(BasicWatchlist):
    """Watchlist entry for tickets."""
    realms = ['ticket']
    fields = {'ticket':{
        'author'    : T_("Author"),
        'changes'   : N_("Changes"),
        # TRANSLATOR: '#' stands for 'number'.
        # This is the header label for a column showing the number
        # of the latest comment.
        'commentnum': N_("Comment #"),
        'unwatch'   : N_("U"),
        'notify'    : N_("Notify"),
        'comment'   : T_("Comment"),
        'attachment': T_("Attachments"),
        # Plus further pairs imported at __init__.
    }}

    default_fields = {'ticket':[
        'id', 'changetime', 'author', 'changes', 'commentnum',
        'unwatch', 'notify', 'comment',
    ]}
    sort_key = {'ticket':int}

    tagsystem = None

    def __init__(self):
        try: # Only works for Trac 0.12, but is not needed for Trac 0.11 anyway
            self.fields['ticket'].update( self.env[TicketSystem].get_ticket_field_labels() )
        except (KeyError, AttributeError):
            pass
        self.fields['ticket']['id'] = self.get_realm_label('ticket')

        try: # Try to support the Tags Plugin
            from tractags.api import TagSystem
            self.tagsystem = self.env[TagSystem]
        except ImportError, e:
            pass
        else:
            if self.tagsystem:
                self.fields['ticket']['tags'] = _("Tags")


    def get_realm_label(self, realm, n_plural=1, astitle=False):
        if astitle:
            # TRANSLATOR: 'ticket(s)' as title
            return ngettext("Ticket", "Tickets", n_plural)
        else:
            # TRANSLATOR: 'ticket(s)' inside a sentence
            return ngettext("ticket", "tickets", n_plural)


    def _get_sql(self, resids, fuzzy, var='id'):
        if isinstance(resids,basestring):
            sql = decode_range_sql( resids ) % {'var':var}
            args = []
        else:
            args = resids
            if (len(resids) == 1):
                sql = ' ' + var + '=%s '
            else:
                sql = ' ' + var + ' IN (' + ','.join(('%s',) * len(resids)) + ') '
        return sql, args


    def resources_exists(self, realm, resids, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy)
        if not sql:
            return []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id
            FROM ticket
            WHERE
        """ + sql, args)
        return [ unicode(v[0]) for v in cursor.fetchall() ]


    def watched_resources(self, realm, resids, user, wl, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy, 'CAST(resid AS decimal)')
        if not sql:
            return []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.log = self.log
        cursor.execute("""
            SELECT resid
            FROM watchlist
            WHERE wluser=%s AND realm='ticket' AND (
        """ + sql + " )", [user] + args)
        return [ unicode(v[0]) for v in cursor.fetchall() ]


    def unwatched_resources(self, realm, resids, user, wl, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy)
        if not sql:
            return []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.log = self.log
        cursor.execute("""
            SELECT id
            FROM ticket
            WHERE id NOT in (
                SELECT CAST(resid as decimal)
                FROM watchlist
                WHERE wluser=%s AND realm='ticket'
            ) AND (
        """ + sql + " )", [user] + args)
        return [ unicode(v[0]) for v in cursor.fetchall() ]


    def get_list(self, realm, wl, req, fields=None):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        context = Context.from_request(req)
        locale = getattr( req, 'locale', LC_TIME)

        ticketlist = []
        extradict = {}
        if not fields:
            fields = set(self.default_fields['ticket'])
        else:
            fields = set(fields)

        if 'changetime' in fields:
            max_changetime = datetime(1970,1,1,tzinfo=utc)
            min_changetime = datetime.now(utc)
        if 'time' in fields:
            max_time = datetime(1970,1,1,tzinfo=utc)
            min_time = datetime.now(utc)


        for sid,last_visit in wl.get_watched_resources( 'ticket', req.authname ):
            ticketdict = {}
            try:
                ticket = Ticket(self.env, sid, db)
                exists = ticket.exists
            except:
                exists = False

            if not exists:
                ticketdict['deleted'] = True
                if 'id' in fields:
                    ticketdict['id'] = sid
                    ticketdict['ID'] = '#' + sid
                if 'author' in fields:
                    ticketdict['author'] = '?'
                if 'changetime' in fields:
                    ticketdict['changedsincelastvisit'] = 1
                    ticketdict['changetime'] = '?'
                    ticketdict['ichangetime'] = 0
                if 'time' in fields:
                    ticketdict['time'] = '?'
                    ticketdict['itime'] = 0
                if 'comment' in fields:
                    ticketdict['comment'] = tag.strong(t_("deleted"), class_='deleted')
                if 'notify' in fields:
                    ticketdict['notify'] =  wl.is_notify(req, 'ticket', sid)
                if 'description' in fields:
                    ticketdict['description'] = ''
                if 'owner' in fields:
                    ticketdict['owner'] = ''
                if 'reporter' in fields:
                    ticketdict['reporter'] = ''
                ticketlist.append(ticketdict)
                continue

            render_elt = lambda x: x
            if not (Chrome(self.env).show_email_addresses or \
                    'EMAIL_VIEW' in req.perm(ticket.resource)):
                render_elt = obfuscate_email_address

            # Copy all requested fields from ticket
            if fields:
                for f in fields:
                    ticketdict[f] = ticket.values.get(f,u'')
            else:
                ticketdict = ticket.values.copy()

            changetime = ticket.time_changed
            if wl.options['attachment_changes']:
                for attachment in Attachment.select(self.env, 'ticket', sid, db):
                    if attachment.date > changetime:
                        changetime = attachment.date
            if 'attachment' in fields:
                attachments = []
                for attachment in Attachment.select(self.env, 'ticket', sid, db):
                    wikitext = u'[attachment:"' + u':'.join([attachment.filename,'ticket',sid]) + u'" ' + attachment.filename  + u']'
                    attachments.extend([tag(', '), format_to_oneliner(self.env, context, wikitext, shorten=False)])
                if attachments:
                    attachments.reverse()
                    attachments.pop()
                ticketdict['attachment'] = moreless(attachments, 5)

            # Changes are special. Comment, commentnum and last author are included in them.
            if 'changes' in fields or 'author' in fields or 'comment' in fields or 'commentnum' in fields:
                changes = []
                # If there are now changes the reporter is the last author
                author  = ticket.values['reporter']
                commentnum = u"0"
                comment = u""
                want_changes = 'changes' in fields
                for date,cauthor,field,oldvalue,newvalue,permanent in ticket.get_changelog(changetime,db):
                    author = cauthor
                    if field == 'comment':
                        if 'commentnum' in fields:
                            ticketdict['commentnum'] = to_unicode(oldvalue)
                        if 'comment' in fields:
                            comment = to_unicode(newvalue)
                            comment = moreless(comment, 200)
                            ticketdict['comment'] = comment
                        if not want_changes:
                            break
                    else:
                        if want_changes:
                            label = self.fields['ticket'].get(field,u'')
                            if label:
                                changes.extend(
                                    [ tag(tag.strong(label), ' ',
                                        render_property_diff(self.env, req, ticket, field, oldvalue, newvalue)
                                        ), tag('; ') ])
                if want_changes:
                    # Remove the last tag('; '):
                    if changes:
                        changes.pop()
                    changes = moreless(changes, 5)
                    ticketdict['changes'] = tag(changes)

            if 'id' in fields:
                ticketdict['id'] = sid
                ticketdict['ID'] = format_to_oneliner(self.env, context, '#' + sid, shorten=True)
            if 'cc' in fields:
                if render_elt == obfuscate_email_address:
                    ticketdict['cc'] = ', '.join([ render_elt(c) for c in ticketdict['cc'].split(', ') ])
            if 'author' in fields:
                ticketdict['author'] = render_elt(author)
            if 'changetime' in fields:
                ichangetime = to_timestamp( changetime )
                ticketdict.update(
                    changetime       = format_datetime( changetime, locale=locale, tzinfo=req.tz ),
                    ichangetime      = ichangetime,
                    changedsincelastvisit = (last_visit < ichangetime and 1 or 0),
                    changetime_delta = pretty_timedelta( changetime ),
                    changetime_link  = req.href.timeline(precision='seconds',
                                       from_=trac_format_datetime ( changetime, 'iso8601', tzinfo=req.tz)))
                if changetime > max_changetime:
                    max_changetime = changetime
                if changetime < min_changetime:
                    min_changetime = changetime
            if 'time' in fields:
                time = ticket.time_created
                ticketdict.update(
                    time             = format_datetime( time, locale=locale, tzinfo=req.tz ),
                    itime            = to_timestamp( time ),
                    time_delta       = pretty_timedelta( time ),
                    time_link        = req.href.timeline(precision='seconds',
                                       from_=trac_format_datetime ( time, 'iso8601', tzinfo=req.tz )))
                if time > max_time:
                    max_time = time
                if time < min_time:
                    min_time = time
            if 'description' in fields:
                description = ticket.values['description']
                description = moreless(description, 200)
                ticketdict['description'] = description
            if 'notify' in fields:
                ticketdict['notify'] = wl.is_notify(req, 'ticket', sid)
            if 'owner' in fields:
                ticketdict['owner'] = render_elt(ticket.values['owner'])
            if 'reporter' in fields:
                ticketdict['reporter'] = render_elt(ticket.values['reporter'])
            if 'tags' in fields and self.tagsystem:
                tags = []
                for t in self.tagsystem.get_tags(req, Resource('ticket', sid)):
                    tags.extend([tag.a(t,href=req.href('tags',q=t)), tag(', ')])
                if tags:
                    tags.pop()
                ticketdict['tags'] = moreless(tags, 10)

            ticketlist.append(ticketdict)

        if 'changetime' in fields:
            extradict['max_changetime'] = format_datetime( max_changetime, locale=locale, tzinfo=req.tz )
            extradict['min_changetime'] = format_datetime( min_changetime, locale=locale, tzinfo=req.tz )
        if 'time' in fields:
            extradict['max_time'] = format_datetime( max_time, locale=locale, tzinfo=req.tz )
            extradict['min_time'] = format_datetime( min_time, locale=locale, tzinfo=req.tz )

        return ticketlist, extradict

_EXTRA_STRINGS = [ _("%(value)s added") ]

# EOF
