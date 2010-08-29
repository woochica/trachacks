"""
 Watchlist Plugin for Trac
 Copyright (c) 2008-2009  Martin Scharrer <martin@scharrer-online.de>
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

from trac.core import *

from  genshi.builder     import  tag, Markup
from  trac.config        import  Configuration
from  trac.db            import  Table, Column, Index, DatabaseManager
from  trac.ticket.model  import  Ticket
from  trac.util.datefmt  import  format_datetime, pretty_timedelta, \
                                 from_utimestamp
from  trac.util.text     import  to_unicode
from  trac.web.api       import  IRequestFilter, IRequestHandler, RequestDone
from  trac.web.chrome    import  ITemplateProvider, add_ctxtnav, add_link, add_script, add_notice
from  trac.web.href      import  Href
from  trac.wiki.model    import  WikiPage
from  urllib             import  quote_plus
from  tracwatchlist.api  import  BasicWatchlist, IWatchlistProvider

__DB_VERSION__ = 3

class WatchlistError(TracError):
    show_traceback = False
    title = 'Watchlist Error'


class WatchlistPlugin(Component):
    """For documentation see http://trac-hacks.org/wiki/WatchlistPlugin"""
    providers = ExtensionPoint(IWatchlistProvider)


    implements( IRequestHandler, IRequestFilter, ITemplateProvider )

    # Enables notification features
    gnotifyu = self.config.getbool('watchlist', 'notifications', False)
    # Enables notification navigation items
    gnotifyctxtnav = self.config.getbool(
                         'watchlist', 'display_notify_navitems', False)
    # Enables notification column in watchlist tables
    gnotifycolumn = self.config.getbool(
                            'watchlist', 'display_notify_column', True)
    # Enables notifications by default for all watchlist entries
    gnotifybydefault = self.config.getbool(
                               'watchlist', 'notify_by_default', False)
    # The user stays at the resource after a watch/unwatch operation
    # and the watchlist page is not displayed.
    gredirectback = self.config.getbool(
                                'watchlist', 'stay_at_resource', False)
    # The user stays at the resource after a notify/do-not-notify operation
    # and the watchlist page is not displayed.
    gredirectback_notify = self.config.getbool(
                          'watchlist', 'stay_at_resource_notify', True)

    # Enables action messages on resource pages.
    gmsgrespage = self.config.getbool(
                   'watchlist', 'show_messages_on_resource_page', True)
    # Enables action messages when going to the watchlist page.
    gmsgwlpage  = self.config.getbool(
                  'watchlist', 'show_messages_on_watchlist_page', True)
    # Enables action messages while on watchlist page.
    gmsgwowlpage = self.config.getbool(
            'watchlist', 'show_messages_while_on_watchlist_page', True)


    gnotify = False

    # Per user setting # FTTB FIXME
    notifyctxtnav = gnotifyctxtnav

    def __init__(self):
      self.realms = []
      self.realm_handler = {}
      for provider in self.providers:
        for realm in provider.get_realms():
          assert realm not in self.realms
          self.realms.append(realm)
          self.realm_handler[realm] = provider
          self.env.log.debug("realm: %s %s" % (realm, str(provider)))
      if self.gnotifyu:
        try:
          # Import methods from WatchSubscriber of the AnnouncerPlugin
          from  announcerplugin.subscribers.watchers  import  WatchSubscriber
          self.wsub = self.env[WatchSubscriber]
          if not self.wsub:
            self.gnotify = False
          else:
            self.gnotify = True
            self.env.log.debug("WS: WatchSubscriber found in announcerplugin")
        except Exception, e:
          try:
            # Import fallback methods for AnnouncerPlugin's dev version
            from  announcer.subscribers.watchers  import  WatchSubscriber
            self.wsub = self.env[WatchSubscriber]
            if not self.wsub:
              self.gnotify = False
            else:
              self.gnotify = True
              self.env.log.debug("WS: WatchSubscriber found in announcer")
          except Exception, ee:
            self.env.log.debug("WS! " + str(e))
            self.env.log.debug("WS! " + str(ee))
            self.gnotify = False

    def is_notify(self, req, realm, resid):
      try:
        return self.wsub.is_watching(req.session.sid, True, realm, resid)
      except Exception, e:
        self.env.log.debug("is_notify error: " + str(e))
        return False

    def set_notify(self, req, realm, resid):
      try:
        self.wsub.set_watch(req.session.sid, True, realm, resid)
      except Exception, e:
        self.env.log.debug("set_notify error: " + str(e))

    def unset_notify(self, req, realm, resid):
      try:
        self.wsub.set_unwatch(req.session.sid, True, realm, resid)
      except Exception, e:
        self.env.log.debug("unset_notify error: " + str(e))

    def _get_sql_names_and_patterns(self, nameorpatternlist):
      import re
      if not nameorpatternlist:
        return [], []
      star  = re.compile(r'(?<!\\)\*')
      ques  = re.compile(r'(?<!\\)\?')
      names = []
      patterns = []
      for norp in nameorpatternlist:
        norp = norp.strip()
        pattern = norp.replace('%',r'\%').replace('_',r'\_')
        pattern_unsub = pattern
        pattern = star.sub('%', pattern)
        pattern = ques.sub('_', pattern)
        if pattern == pattern_unsub:
          names.append(norp)
        else:
          pattern = pattern.replace('\*','*').replace('\?','?')
          patterns.append(pattern)
      return names, patterns

    def _sql_pattern_unescape(self, pattern):
      import re
      percent    = re.compile(r'(?<!\\)%')
      underscore = re.compile(r'(?<!\\)_')
      pattern = pattern.replace('*','\*').replace('?','\?')
      pattern = percent.sub('*', pattern)
      pattern = underscore.sub('?', pattern)
      pattern = pattern.replace('\%','%').replace('\_','_')
      return pattern

    def _convert_pattern(self, pattern):
        # needs more work, excape sequences, etc.
        return pattern.replace('*','%').replace('?','_')

    ### methods for IRequestHandler
    def match_request(self, req):
        return req.path_info.startswith("/watchlist")

    def _save_user_settings(self, user, settings):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.log = self.env.log

        settingsstr = "&".join([ "=".join(kv) for kv in settings.items()])

        cursor.execute("""
          SELECT count(*)
            FROM watchlist_settings
           WHERE wluser=%s
           LIMIT 0,1
        """, (user,)
        )
        ex = cursor.fetchone()
        if not ex or not int(ex[0]):
          cursor.execute("""
            INSERT
              INTO watchlist_settings
            VALUES (%s,%s)
          """, (user, settingsstr)
          )
        else:
          cursor.execute("""
            UPDATE watchlist_settings
               SET settings=%s
             WHERE wluser=%s
          """, (settingsstr, user)
          )

        db.commit()
        return True

    def _get_user_settings(self, user):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT settings
            FROM watchlist_settings
           WHERE wluser = %s
        """, (user,)
        )

        try:
          (settingsstr,) = cursor.fetchone()
          return dict([ kv.split('=') for kv in settingsstr.split("&") ])
        except:
          return dict()


    def process_request(self, req):
        user  = to_unicode( req.authname )
        realm = to_unicode( req.args.get('realm', u'') )
        resid = req.args.get('resid', u'')
        resids = []
        if not isinstance(resid,(list,tuple)):
          resid = [resid]
        for r in resid:
          resids.extend(r.replace(',',' ').split())
        action = req.args.get('action','view')
        names,patterns = self._get_sql_names_and_patterns( resids )
        single = len(names) == 1 and not patterns
        async = req.args.get('async', 'false') == 'true'

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if not user or user == 'anonymous':
            raise WatchlistError(
                    tag( "Please ", tag.a("log in", href=req.href('login')),
                        " to view or change your watchlist!" ) )

        wldict = req.args.copy()
        wldict['perm']   = req.perm
        wldict['realms'] = self.realms
        wldict['error']  = False
        wldict['notify'] = self.gnotify and self.gnotifycolumn
        wldict['user_settings'] = self._get_user_settings(user)

        onwatchlistpage = req.environ.get('HTTP_REFERER','').find(req.href.watchlist()) != -1
        redirectback = self.gredirectback and single and not onwatchlistpage
        redirectback_notify = self.gredirectback_notify and single and not \
                              onwatchlistpage

        if onwatchlistpage:
          wldict['show_messages'] = self.gmsgwowlpage
        else:
          wldict['show_messages'] = self.gmsgwlpage

        new_res = []
        del_res = []
        alw_res = []
        err_res = []
        err_pat = []
        if action == "watch":
          handler = self.realm_handler[realm]
          if names:
            reses = list(handler.res_list_exists(realm, names))

            sql = """
              SELECT resid
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
            """ + ",".join(("%s",) * len(names)) + ")"
            cursor.execute( sql, [user,realm] + names)
            alw_res = [ res[0] for res in cursor.fetchall() ]
            new_res.extend(set(reses).difference(alw_res))
            err_res.extend(set(names).difference(reses))
          for pattern in patterns:
            reses = list(handler.res_pattern_exists(realm, pattern))

            if not reses:
              err_pat.append(self._sql_pattern_unescape(pattern))
            else:
              cursor.execute("""
                SELECT resid
                  FROM watchlist
                 WHERE wluser=%s AND realm=%s AND resid LIKE (%s)
              """, (user,realm,pattern)
              )
              watched_res = [ res[0] for res in cursor.fetchall() ]
              alw_res.extend(set(reses).intersection(watched_res))
              new_res.extend(set(reses).difference(alw_res))

          if new_res:
            cursor.log = self.env.log
            cursor.executemany("""
              INSERT
                INTO watchlist (wluser, realm, resid)
              VALUES (%s,%s,%s)
            """, [(user, realm, res) for res in new_res]
            )
            db.commit()

          action = "view"
          if self.gmsgrespage and not onwatchlistpage and redirectback:
            req.session['watchlist_message'] = 'You are now watching this resource.'
          if self.gnotify and self.gnotifybydefault:
            for res in new_res:
              self.set_notify(req, realm, res)
            db.commit()
          if redirectback:
            req.redirect(req.href(realm,names[0]))
            raise RequestDone

        elif action == "unwatch":
          if names:
            sql = """
              SELECT resid
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
            """ + ",".join(("%s",) * len(names)) + ")"
            cursor.execute( sql, [user,realm] + names)
            reses = [ res[0] for res in cursor.fetchall() ]
            del_res.extend(reses)
            err_res.extend(set(names).difference(reses))

            sql = """
              DELETE
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
              """ + ",".join(("%s",) * len(names)) + ")"
            cursor.execute( sql, [user,realm] + names)
          for pattern in patterns:
            cursor.execute("""
              SELECT resid
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND resid LIKE %s
            """, (user,realm,pattern)
            )
            reses = [ res[0] for res in cursor.fetchall() ]
            if not reses:
              err_pat.append(self._sql_pattern_unescape(pattern))
            else:
              del_res.extend(reses)
              cursor.execute("""
                DELETE
                  FROM watchlist
                 WHERE wluser=%s AND realm=%s AND resid LIKE %s
              """, (user,realm,pattern)
              )
          db.commit()

          action = "view"
          if self.gmsgrespage and not onwatchlistpage and redirectback:
            req.session['watchlist_message'] = 'You are no longer watching this resource.'
          if self.gnotify and self.gnotifybydefault:
            for res in del_res:
              self.unset_notify(req, realm, res)
            db.commit()
          if redirectback:
            req.redirect(req.href(realm,names[0]))
            raise RequestDone

        wldict['del_res'] = del_res
        wldict['err_res'] = err_res
        wldict['err_pat'] = err_pat
        wldict['new_res'] = new_res
        wldict['alw_res'] = alw_res

        if action == "notifyon":
            if self.gnotify:
              for res in resids:
                self.set_notify(req, realm, res)
              db.commit()
            if redirectback_notify and not async:
              if self.gmsgrespage:
                req.session['watchlist_notify_message'] = (
                  'You are now receiving '
                  'change notifications about this resource.')
              req.redirect(req.href(realm,resids[0]))
              raise RequestDone
            action = "view"
        elif action == "notifyoff":
            if self.gnotify:
              for res in resids:
                self.unset_notify(req, realm, res)
              db.commit()
            if redirectback_notify and not async:
              if self.gmsgrespage:
                req.session['watchlist_notify_message'] = (
                  'You are no longer receiving '
                  'change notifications about this resource.')
              req.redirect(req.href(realm,resids[0]))
              raise RequestDone
            action = "view"

        if async:
          req.send("",'text/plain', 200)
          raise RequestDone

        if action == "view":
            for (xrealm,handler) in self.realm_handler.iteritems():
              if handler.has_perm(xrealm, req.perm):
                wldict[xrealm + 'list'] = handler.get_list(xrealm, self, req)
                name = handler.get_realm_label(xrealm, plural=True)
                add_ctxtnav(req, "Watched " + name.capitalize(), href=req.href('watchlist#' + name))
            return ("watchlist.html", wldict, "text/html")
        else:
            raise WatchlistError("Invalid watchlist action '%s'!" % action)


    def has_watchlist(self, user):
        """Checks if user has a non-empty watchlist."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT count(*)
            FROM watchlist
           WHERE wluser=%s;
        """, (user,)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True

    def res_exists(self, realm, resid):
        return self.realm_handler[realm].res_exists(realm, resid)

    def is_watching(self, realm, resid, user):
        """Checks if user watches the given element."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT count(*)
            FROM watchlist
           WHERE realm=%s AND resid=%s AND wluser=%s;
        """, (realm, to_unicode(resid), user)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True

    ### methods for IRequestFilter
    def post_process_request(self, req, template, data, content_type):
        msg = req.session.get('watchlist_message',[])
        if msg:
          add_notice(req, msg)
          del req.session['watchlist_message']
        msg = req.session.get('watchlist_notify_message',[])
        if msg:
          add_notice(req, msg)
          del req.session['watchlist_notify_message']

        # Extract realm and resid from path:
        parts = req.path_info[1:].split('/',1)

        # Handle special case for '/' and '/wiki'
        if len(parts) == 0 or not parts[0]:
            parts = ["wiki", "WikiStart"]
        elif len(parts) == 1:
            parts.append("WikiStart")

        realm, resid = parts[:2]

        if realm not in self.realms or not \
                self.realm_handler[realm].has_perm(realm, req.perm):
            return (template, data, content_type)

        href = Href(req.base_path)
        user = req.authname
        if user and user != "anonymous":
            if self.is_watching(realm, resid, user):
                add_ctxtnav(req, "Unwatch",
                    href=req.href('watchlist', action='unwatch',
                    resid=resid, realm=realm),
                    title="Remove %s from watchlist" % realm)
            else:
                add_ctxtnav(req, "Watch",
                    href=req.href('watchlist', action='watch',
                    resid=resid, realm=realm),
                    title="Add %s to watchlist" % realm)
            if self.gnotify and self.notifyctxtnav:
              if self.is_notify(req, realm, resid):
                add_ctxtnav(req, "Do not Notify me",
                    href=req.href('watchlist', action='notifyoff',
                    resid=resid, realm=realm),
                    title="Do not notify me if %s changes" % realm)
              else:
                add_ctxtnav(req, "Notify me",
                    href=req.href('watchlist', action='notifyon',
                    resid=resid, realm=realm),
                    title="Notify me if %s changes" % realm)

        return (template, data, content_type)


    def pre_process_request(self, req, handler):
        return handler

    # ITemplateProvider methods:
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('watchlist', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [ resource_filename(__name__, 'templates') ]



class WikiWatchlist(BasicWatchlist):
    realms = ['wiki']

    def res_exists(self, realm, resid):
      return WikiPage(self.env, resid).exists

    def res_pattern_exists(self, realm, pattern):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute("""
        SELECT name
          FROM wiki
         WHERE name
          LIKE (%s)
      """, (pattern,)
      )
      return [ vals[0] for vals in cursor.fetchall() ]

    def get_list(self, realm, wl, req):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      user = req.authname
      wikilist = []
      # Watched wikis which got deleted:
      cursor.execute("""
        SELECT resid
          FROM watchlist
         WHERE realm='wiki' AND wluser=%s AND
               resid NOT IN (
          SELECT DISTINCT name
                     FROM wiki
          );
        """, (user,)
        )

      for (name,) in cursor.fetchall():
          notify = False
          if wl.gnotify:
            notify = wl.is_notify(req, 'wiki', name)
          wikilist.append({
              'name' : name,
              'author' : '?',
              'datetime' : '?',
              'comment' : tag.strong("DELETED!", class_='deleted'),
              'notify'  : notify,
              'deleted' : True,
          })
      # Existing watched wikis:
      cursor.execute("""
        SELECT name,author,time,version,comment
          FROM wiki AS w1
         WHERE name IN (
           SELECT resid
             FROM watchlist
            WHERE wluser=%s AND realm='wiki'
           )
               AND version=(
           SELECT MAX(version)
             FROM wiki AS w2
            WHERE w1.name=w2.name
           )
         ORDER BY time DESC;
      """, (user,)
      )

      wikis = cursor.fetchall()
      for name,author,time,version,comment in wikis:
          notify = False
          if wl.gnotify:
            notify = wl.is_notify(req, 'wiki', name)
          wikilist.append({
              'name' : name,
              'author' : author,
              'version' : version,
              'datetime' : format_datetime(from_utimestamp(time)),
              'timedelta' : pretty_timedelta(from_utimestamp(time)),
              'timeline_link' : req.href.timeline(precision='seconds',
                  from_=format_datetime(from_utimestamp(time),'iso8601')),
              'comment' : comment,
              'notify'  : notify,
          })
      return wikilist


class TicketWatchlist(BasicWatchlist):
    realms = ['ticket']

    def res_exists(self, realm, resid):
      try:
        return Ticket(self.env, int(resid)).exists
      except:
        return False

    def res_pattern_exists(self, realm, pattern):
      if pattern == '%':
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT id
            FROM ticket
        """
        )
        return [ vals[0] for vals in cursor.fetchall() ]
      else:
        return []

    def get_list(self, realm, wl, req):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      user = req.authname
      ticketlist = []
      cursor.execute("""
        SELECT id,type,time,changetime,summary,reporter
          FROM ticket
         WHERE id IN (
           SELECT CAST(resid AS decimal)
             FROM watchlist
            WHERE wluser=%s AND realm='ticket'
           )
         GROUP BY id,type,time,changetime,summary,reporter
         ORDER BY changetime DESC;
      """, (user,)
      )
      tickets = cursor.fetchall()
      for id,type,time,changetime,summary,reporter in tickets:
          self.commentnum = 0
          self.comment    = ''

          notify = False
          if wl.gnotify:
            notify = wl.is_notify(req, 'ticket', id)

          cursor.execute("""
            SELECT author,field,oldvalue,newvalue
              FROM ticket_change
             WHERE ticket=%s and time=%s
             ORDER BY field DESC;
          """, (id, changetime)
          )

          def format_change(field,oldvalue,newvalue):
              """Formats tickets changes."""
              fieldtag = tag.strong(field)
              if field == 'cc':
                  oldvalues = set(oldvalue and oldvalue.split(', ') or [])
                  newvalues = set(newvalue and newvalue.split(', ') or [])
                  added   = newvalues.difference(oldvalues)
                  removed = oldvalues.difference(newvalues)
                  strng = fieldtag
                  if added:
                      strng += tag(" ", tag.em(', '.join(added)), " added")
                  if removed:
                      if added:
                          strng += tag(', ')
                      strng += tag(" ", tag.em(', '.join(removed)), " removed")
                  return strng
              elif field == 'description':
                  return fieldtag + tag(" modified (", tag.a("diff",
                      href=req.href('ticket',id,action='diff',
                                version=self.commentnum)), ")")
              elif field == 'comment':
                  self.commentnum = oldvalue
                  self.comment    = newvalue
                  return tag("")
              elif not oldvalue:
                  return fieldtag + tag(" ", tag.em(newvalue), " added")
              elif not newvalue:
                  return fieldtag + tag(" ", tag.em(oldvalue), " deleted")
              else:
                  return fieldtag + tag(" changed from ", tag.em(oldvalue),
                                        " to ", tag.em(newvalue))

          changes = []
          author  = reporter
          for author_,field,oldvalue,newvalue in cursor.fetchall():
              author = author_
              changes.extend( [format_change(field,oldvalue,newvalue), tag("; ") ])
          # changes holds list of formatted changes interleaved with
          # tag('; '). The first change is always the comment which
          # returns an empty tag, so we skip the first two elements
          # [tag(''), tag('; ')] and remove the last tag('; '):
          changes = changes and tag(changes[2:-1]) or tag()
          ticketlist.append({
              'id' : to_unicode(id),
              'type' : type,
              'author' : author,
              'commentnum': to_unicode(self.commentnum),
              'comment' : len(self.comment) <= 250 and self.comment or self.comment[:250] + '...',
              'datetime' : format_datetime(from_utimestamp(changetime)),
              'timedelta' : pretty_timedelta(from_utimestamp(changetime)),
              'timeline_link' : req.href.timeline(precision='seconds',
                  from_=format_datetime(from_utimestamp(time),'iso8601')),
              'changes' : changes,
              'summary' : summary,
              'notify'  : notify,
          })
      return ticketlist

class ExampleWatchlist(Component):
    #implements( IWatchlistProvider )

    def get_realms(self):
      return ('example',)

    def get_realm_label(self, realm, plural=False):
      return plural and 'examples' or 'example'

    def res_exists(self, realm, resid):
      return True

    def res_list_exists(self, realm, reslist):
      return []

    def res_pattern_exists(self, realm, pattern):
      return True

    def has_perm(self, realm, perm):
      return True

    def get_list(self, realm, wl, req):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      user = req.authname
      examplelist = []
      cursor.execute("""
        SELECT resid
          FROM watchlist
         WHERE wluser=%s AND realm='example'
      """, (user,)
      )
      examples = cursor.fetchall()
      for (name,) in examples:
        examplelist.append({'name':name})
      return examplelist

