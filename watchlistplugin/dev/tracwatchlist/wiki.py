# -*- coding: utf-8 -*-
"""
 Watchlist Plugin for Trac
 Copyright (c) 2008-2010  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  trac.core              import  *
from  genshi.builder         import  tag, Markup
from  trac.wiki.model        import  WikiPage
from  trac.wiki.formatter    import  format_to_oneliner
from  trac.util.datefmt      import  pretty_timedelta, to_datetime, \
                                     datetime, utc, to_timestamp
from  trac.util.text         import  to_unicode, obfuscate_email_address

from  trac.util.datefmt      import  format_datetime as trac_format_datetime
from  trac.web.chrome        import  Chrome
from  trac.mimeview.api      import  Context
from  trac.resource          import  Resource
from  trac.attachment        import  Attachment

from  tracwatchlist.api      import  BasicWatchlist
from  tracwatchlist.translation import  _, N_, T_, t_, tag_, gettext, ngettext
from  tracwatchlist.util     import  moreless, format_datetime, LC_TIME,\
                                     convert_to_sql_wildcards


class WikiWatchlist(BasicWatchlist):
    """Watchlist entry for wiki pages."""
    realms = ['wiki']
    fields = {'wiki':{
        'changetime': T_("Modified"),
        'author'    : T_("Author"),
        'version'   : T_("Version"),
        'diff'      : T_("Diff"),
        'history'   : T_("History"),
        # TRANSLATOR: Abbreviated label for 'unwatch' column header.
        # Should be a single character to not widen the column.
        'unwatch'   : N_("U"),
        # TRANSLATOR: Label for 'notify' column header.
        # Should tell the user that notifications can be switched on or off
        # with the check-boxes in this column.
        'notify'    : N_("Notify"),
        'comment'   : T_("Comment"),

        'readonly'  : N_("read-only"),
        # T#RANSLATOR: IP = Internet Protocol (address)
        #'ipnr'      : N_("IP"), # Note: not supported by Trac 0.12 WikiPage class
    }}
    default_fields = {'wiki':[
        'name', 'changetime', 'author', 'version', 'diff',
        'history', 'unwatch', 'notify', 'comment',
    ]}
    tagsystem = None


    def __init__(self):
        self.fields['wiki']['name'] = self.get_realm_label('wiki')
        try: # Try to support the Tags Plugin
            from tractags.api import TagSystem
            self.tagsystem = self.env[TagSystem]
        except ImportError, e:
            pass
        else:
            if self.tagsystem:
                self.fields['wiki']['tags'] = _("Tags")


    def get_realm_label(self, realm, n_plural=1):
        return ngettext("Wiki Page", "Wiki Pages", n_plural)


    def resources_exists(self, realm, resids, fuzzy=0):
        if not resids:
            return []
        if isinstance(resids,basestring):
            if fuzzy:
                resids += '*'
            resids = convert_to_sql_wildcards(resids).replace(',',' ').split()
            sql = ' OR '.join((' name LIKE %s ESCAPE \'\\\' ',) * len(resids))
        else:
            resids = list(resids)
            if (len(resids) == 1):
                sql = ' name=%s '
            else:
                sql = ' name IN (' + ','.join(('%s',) * len(resids)) + ') '
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT name
            FROM wiki
            WHERE
        """ + sql, resids)
        ret = [ unicode(v[0]) for v in cursor.fetchall() ]
        return ret


    def get_list(self, realm, wl, req, fields=None):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        user = req.authname
        locale = getattr( req, 'locale', LC_TIME)
        context = Context.from_request(req)
        wikilist = []
        extradict = {}
        if not fields:
            fields = set(self.default_fields['wiki'])
        else:
            fields = set(fields)

        if 'changetime' in fields:
            max_changetime = datetime(1970,1,1,tzinfo=utc)
            min_changetime = datetime.now(utc)

        for name, last_visit in wl.get_watched_resources( 'wiki', req.authname ):
            wikipage = WikiPage(self.env, name, db=db)
            wikidict = {}

            if not wikipage.exists:
                wikidict['deleted'] = True
                if 'name' in fields:
                    wikidict['name'] = name
                if 'author' in fields:
                    wikidict['author'] = '?'
                if 'changetime' in fields:
                    wikidict['changedsincelastvisit'] = 1
                    wikidict['changetime'] = '?'
                    wikidict['ichangetime'] = 0
                if 'comment' in fields:
                    wikidict['comment'] = tag.strong(t_("deleted"), class_='deleted')
                if 'notify' in fields:
                    wikidict['notify'] =  wl.is_notify(req, 'wiki', name)
                wikilist.append(wikidict)
                continue

            comment = wikipage.comment
            changetime = wikipage.time
            author = wikipage.author
            if wl.options['attachment_changes']:
                latest_attachment = None
                for attachment in Attachment.select(self.env, 'wiki', name, db):
                    if attachment.date > changetime:
                        latest_attachment = attachment
                if latest_attachment:
                    changetime = latest_attachment.date
                    author = latest_attachment.author
                    if 'comment' in fields:
                        wikitext = '[attachment:"' + ':'.join([latest_attachment.filename,'wiki',name]) + \
                                   '" ' + latest_attachment.filename  + ']'
                        desc = latest_attachment.description
                        comment = tag(tag_("Attachment %(attachment)s added",\
                                attachment=format_to_oneliner(self.env, context, wikitext, shorten=False)),
                                desc and ': ' or '.', moreless(desc,10))
            if 'attachment' in fields:
                attachments = []
                for attachment in Attachment.select(self.env, 'wiki', name, db):
                    wikitext = '[attachment:"' + ':'.join([attachment.filename,'wiki',name]) + '" ' + attachment.filename  + ']'
                    attachments.extend([tag(', '), format_to_oneliner(self.env, context, wikitext, shorten=False)])
                if attachments:
                    attachments.reverse()
                    attachments.pop()
                ticketdict['attachment'] = moreless(attachments, 5)
            if 'name' in fields:
                wikidict['name'] = name
            if 'author' in fields:
                if not (Chrome(self.env).show_email_addresses or
                        'EMAIL_VIEW' in req.perm(wikipage.resource)):
                    wikidict['author'] = obfuscate_email_address(author)
                else:
                    wikidict['author'] = author
            if 'version' in fields:
                wikidict['version'] = unicode(wikipage.version)
            if 'changetime' in fields:
                wikidict['changetime'] = format_datetime( changetime, locale=locale, tzinfo=req.tz )
                wikidict['ichangetime'] = to_timestamp( changetime )
                wikidict['changedsincelastvisit'] = last_visit < wikidict['ichangetime'] and 1 or 0
                wikidict['timedelta'] = pretty_timedelta( changetime )
                wikidict['timeline_link'] = req.href.timeline(precision='seconds',
                    from_=trac_format_datetime ( changetime, 'iso8601', tzinfo=req.tz))
                if changetime > max_changetime:
                    max_changetime = changetime
                if changetime < min_changetime:
                    min_changetime = changetime
            if 'comment' in fields:
                comment = moreless(comment or "", 200)
                wikidict['comment'] = comment
            if 'notify' in fields:
                wikidict['notify']   = wl.is_notify(req, 'wiki', name)
            if 'readonly' in fields:
                wikidict['readonly'] = wikipage.readonly and t_("yes") or t_("no")
            if 'tags' in fields and self.tagsystem:
                tags = []
                for t in self.tagsystem.get_tags(req, Resource('wiki', name)):
                    tags.extend([tag.a(t,href=req.href('tags',q=t)), tag(', ')])
                if tags:
                    tags.pop()
                wikidict['tags'] = moreless(tags, 10)
            #if 'ipnr' in fields:
            #    wikidict['ipnr'] = wikipage.ipnr,  # Note: Not supported by Trac 0.12
            wikilist.append(wikidict)

        if 'changetime' in fields:
            extradict['max_changetime'] = format_datetime( max_changetime, locale=locale, tzinfo=req.tz )
            extradict['min_changetime'] = format_datetime( min_changetime, locale=locale, tzinfo=req.tz )

        return wikilist, extradict

# EOF
