# -*- coding: utf-8 -*-
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

from  pkg_resources          import  resource_filename
from  urllib                 import  quote_plus

from  genshi.builder         import  tag, Markup
from  trac.config            import  BoolOption
from  trac.core              import  *
from  trac.db                import  Table, Column, Index, DatabaseManager
from  trac.ticket.model      import  Ticket
from  trac.util.translation  import  domain_functions
from  trac.util.datefmt      import  format_datetime, pretty_timedelta, \
                                     from_utimestamp
from  trac.util.text         import  to_unicode
from  trac.web.api           import  IRequestFilter, IRequestHandler, \
                                     RequestDone
from  trac.web.chrome        import  ITemplateProvider, add_ctxtnav, \
                                     add_link, add_script, add_notice
from  trac.web.href          import  Href
from  trac.wiki.model        import  WikiPage

from  trac.prefs.api         import  IPreferencePanelProvider

from  tracwatchlist.api      import  BasicWatchlist, IWatchlistProvider


 
__DB_VERSION__ = 3

add_domain, _, tag_ = \
    domain_functions('watchlist', ('add_domain', '_', 'tag_'))


class WatchlistError(TracError):
    show_traceback = False
    title = _("Watchlist Error")


class WatchlistPlugin(Component):
    """For documentation see http://trac-hacks.org/wiki/WatchlistPlugin"""
    providers = ExtensionPoint(IWatchlistProvider)

    implements( IRequestHandler, IRequestFilter, ITemplateProvider ) 
    #, IPreferencePanelProvider ) # Disabled for now. Needs code dublication and isn't really necessary 


    options = {
        'notifications': ( False, _("Notifications")),
        'display_notify_navitems': ( False, _("Display notification navigation items")),
        'display_notify_column': ( True, _("Display notification column in watchlist tables")),
        'notify_by_default': ( False, _("Enable notifications by default for all watchlist entries")),
        'stay_at_resource': ( False, _("The user stays at the resource after a watch/unwatch operation and the watchlist page is not displayed")),
        'stay_at_resource_notify': ( True, _("The user stays at the resource after a notify/do-not-notify operation and the watchlist page is not displayed")),
        'show_messages_on_resource_page': ( True, _("Action messages are shown on resource pages")),
        'show_messages_on_watchlist_page': ( True, _("Action messages are shown when going to the watchlist page")),
        'show_messages_while_on_watchlist_page': ( True, _("Show action messages while on watchlist page")),
        'autocomplete_inputs': ( True, _("Autocomplete input fields (add/remove resources)")),
        'dynamic_tables': ( True, _("Dynamic watchlist tables")),
    }

    gsettings = dict( [ (name, BoolOption('watchlist',name,data[0],data[1]) ) for (name,data) in options.iteritems() ] )

    wsub = None

    def __init__(self):
      self.realms = []
      self.realm_handler = {}

      # bind the 'watchlist' catalog to the specified locale directory
      locale_dir = resource_filename(__name__, 'locale')
      add_domain(self.env.path, locale_dir)

      for provider in self.providers:
        for realm in provider.get_realms():
          assert realm not in self.realms
          self.realms.append(realm)
          self.realm_handler[realm] = provider
          self.log.debug("realm: %s %s" % (realm, str(provider)))

      try:
          # Import methods from WatchSubscriber of the AnnouncerPlugin
          from  announcerplugin.subscribers.watchers  import  WatchSubscriber
          self.wsub = self.env[WatchSubscriber]
          if self.wsub:
            self.log.debug("WS: WatchSubscriber found in announcerplugin")
      except Exception, e:
          try:
            # Import fallback methods for AnnouncerPlugin's dev version
            from  announcer.subscribers.watchers  import  WatchSubscriber
            self.wsub = self.env[WatchSubscriber]
            if self.wsub:
              self.log.debug("WS: WatchSubscriber found in announcer")
          except Exception, ee:
            self.log.debug("WS! " + str(e))
            self.log.debug("WS! " + str(ee))
            self.wsub = None

    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        """Return a list of available preference panels.
        
        The items returned by this function must be tuple of the form
        `(panel, label)`.
        """
        user  = to_unicode( req.authname )
        if not user or user == 'anonymous':
          return []
        return [('watchlist',_("Watchlist"))]

    def render_preference_panel(self, req, panel):
        """Process a request for a preference panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        settings = self.get_settings( req.authname )

        if req.method == 'POST':
            self._handle_settings(req, settings);
            req.redirect(req.href.prefs(panel))

        return ('watchlist_prefs_main.html', { 'settings': settings, 'options': self.options, 'realms': self.realms })

    def _handle_settings(self, req, settings):
        newoptions = req.args.get('options',[])
        for k in settings.keys():
          settings[k] = k in newoptions
        for realm in self.realms:
          try:
            settings[realm + '_columns'] = req.args.get(realm + '_columns')
          except:
            pass
        self._save_user_settings(req.authname, settings)
        # Clear session cache for nav items
        try:
            del req.session['watchlist_display_notify_navitems']
        except:
            pass

    def get_settings(self, user):
        settings = {}
        settings.update( [ ( name,self.config.getbool('watchlist',name) ) for name in self.options.keys() ] )
        settings.update( self._get_user_settings(user) )
        return settings

    def is_notify(self, req, realm, resid):
      try:
        return self.wsub.is_watching(req.session.sid, True, realm, resid)
      except Exception, e:
        self.log.debug("is_notify error: " + str(e))
        return False

    def set_notify(self, req, realm, resid):
      try:
        self.wsub.set_watch(req.session.sid, True, realm, resid)
      except Exception, e:
        self.log.debug("set_notify error: " + str(e))

    def unset_notify(self, req, realm, resid):
      try:
        self.wsub.set_unwatch(req.session.sid, True, realm, resid)
      except Exception, e:
        self.log.debug("unset_notify error: " + str(e))

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
        #cursor.log = self.log

        settingsstr = "&".join([ "=".join([k,unicode(v)]) for k,v in settings.iteritems()])

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
           WHERE wluser=%s
        """, (user,))

        try:
          def strtoval (val):
            if   val == 'True':
              return True
            elif val == 'False':
              return False
            else:
              return val
          (settingsstr,) = cursor.fetchone()
          self.log.debug("WL SET: " + settingsstr)
          d = dict([
              (k,strtoval(v)) for k,v in [ kv.split('=') for kv in settingsstr.split("&") ]
          ])
          self.log.debug("WL SETd: " + unicode(d))
          return d
        except Exception, e:
          self.log.debug("WL get user settings: " + unicode(e))
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
                    tag(_("Please "), tag.a(_("log in"),
                         href=req.href('login')),
                         _(" to view or change your watchlist!"))
            )

        wldict = req.args.copy()
        wldict['action'] = action

        settings = self.get_settings( user )
        # Needed here to get updated settings
        if action == "save":
          self._handle_settings(req, settings)
          action = "view"

        settings = self.get_settings( user )
        wldict['perm']   = req.perm
        wldict['realms'] = self.realms
        wldict['error']  = False
        wldict['notifications'] = bool(self.wsub and settings['notifications'] and settings['display_notify_column'])
        wldict['options'] = self.options
        wldict['settings'] = settings
        wldict['available_columns'] = {}
        wldict['default_columns'] = {}
        for r in self.realms:
            wldict['available_columns'][r],wldict['default_columns'][r] = self.realm_handler[r].get_columns(r)
        wldict['active_columns'] = {}
        for r in self.realms:
            cols = settings.get(r + '_columns','').split(',')
            self.log.debug( "WL SC = " + unicode(cols) )
            if not cols or cols == ['']:
                cols = wldict['default_columns'].get(r,[])
                self.log.debug( "WL EC = " + unicode(cols) )
            wldict['active_columns'][r] = cols
        self.log.debug( "WL DC = " + unicode(wldict['default_columns']) )
        self.log.debug( "WL AC = " + unicode(wldict['active_columns']) )

        onwatchlistpage = req.environ.get('HTTP_REFERER','').find(
                          req.href.watchlist()) != -1
        redirectback = settings['stay_at_resource'] and single and not onwatchlistpage
        redirectback_notify = settings['stay_at_resource_notify'] and single and not \
                              onwatchlistpage

        if onwatchlistpage:
          wldict['show_messages'] = settings['show_messages_while_on_watchlist_page']
        else:
          wldict['show_messages'] = settings['show_messages_on_watchlist_page']

        new_res = []
        del_res = []
        alw_res = []
        err_res = []
        err_pat = []
        if action == "watch":
          handler = self.realm_handler[realm]
          if names:
            reses = list(handler.res_list_exists(realm, names))

            sql = ("""
              SELECT resid
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
            """ + ",".join(("%s",) * len(names)) + ")"
            )
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
            #cursor.log = self.log
            cursor.executemany("""
              INSERT
                INTO watchlist (wluser, realm, resid)
              VALUES (%s,%s,%s)
            """, [(user, realm, res) for res in new_res]
            )
            db.commit()

          action = "view"
          if settings['show_messages_on_resource_page'] and not onwatchlistpage and redirectback:
            req.session['watchlist_message'] = _(
              "You are now watching this resource."
            )
          if self.wsub and settings['notifications'] and settings['notify_by_default']:
            for res in new_res:
              self.set_notify(req, realm, res)
            db.commit()
          if redirectback:
            req.redirect(req.href(realm,names[0]))
            raise RequestDone

        elif action == "unwatch":
          if names:
            sql = ("""
              SELECT resid
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
            """ + ",".join(("%s",) * len(names)) + ")"
            )
            cursor.execute( sql, [user,realm] + names)
            reses = [ res[0] for res in cursor.fetchall() ]
            del_res.extend(reses)
            err_res.extend(set(names).difference(reses))

            sql = ("""
              DELETE
                FROM watchlist
               WHERE wluser=%s AND realm=%s AND
                     resid IN (
            """ + ",".join(("%s",) * len(names)) + ")"
            )
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
          if settings['show_messages_on_resource_page'] and not onwatchlistpage and redirectback:
            req.session['watchlist_message'] = _(
              "You are no longer watching this resource."
            )
          if self.wsub and settings['notifications'] and settings['notify_by_default']:
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
            if self.wsub and settings['notifications']:
              for res in resids:
                self.set_notify(req, realm, res)
              db.commit()
            if redirectback_notify and not async:
              if settings['show_messages_on_resource_page']:
                req.session['watchlist_notify_message'] = _(
                  """
                  You are now receiving change notifications
                  about this resource.
                  """
                )
              req.redirect(req.href(realm,resids[0]))
              raise RequestDone
            action = "view"
        elif action == "notifyoff":
            if self.wsub and settings['notifications']:
              for res in resids:
                self.unset_notify(req, realm, res)
              db.commit()
            if redirectback_notify and not async:
              if settings['show_messages_on_resource_page']:
                req.session['watchlist_notify_message'] = _(
                  """
                  You are no longer receiving
                  change notifications about this resource.
                  """
                )
              req.redirect(req.href(realm,resids[0]))
              raise RequestDone

            action = "view"

        if action == "search":
          query = req.args.get('q', u'')
          handler = self.realm_handler[realm]
          found = handler.res_pattern_exists(realm, query + '%')
          db = self.env.get_db_cnx()
          cursor = db.cursor()
          cursor.execute("""
            SELECT resid
              FROM watchlist
            WHERE realm=%s AND wluser=%s
          """, (realm, user)
          )
          watched = [a[0] for a in cursor.fetchall()]
          notwatched = list(set(found).difference(set(watched)))
          notwatched.sort()
          req.send( unicode('\n'.join(notwatched) + '\n').encode("utf-8"), 'text/plain', 200 )
          raise RequestDone


        if async:
          req.send("",'text/plain', 200)
          raise RequestDone

        wldict['th'] = {
          'name': _("Page"), 'datetime': _("Last Changed At"),
          'author': _("By"), 'version': _("Version"), 'diff': _("Diff"),
          'history': _("History"), 'unwatch': _("U"), 'notify': _("Notify"),
          'comment': _("Comment"), 'id': _("Ticket"),
          'commentnum': _("Comment #"), 'changes': _("Changes")
        }

        if action == "view":
            for (xrealm,handler) in self.realm_handler.iteritems():
              if handler.has_perm(xrealm, req.perm):
                wldict[xrealm + 'list'] = handler.get_list(xrealm, self, req)
                name = handler.get_realm_label(xrealm, plural=True)
                add_ctxtnav(req, _("Watched %s") % name.capitalize(),
                            href=req.href('watchlist') + '#' + name)
            return ("watchlist.html", wldict, "text/html")
        else:
            raise WatchlistError(_("Invalid watchlist action '%s'!") % action)


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

        user  = to_unicode( req.authname )

        notify = 'False'
        try:
            notify = req.session['watchlist_display_notify_navitems']
            self.log.debug("WL: Reusing settings for navitems.")
        except:
            self.log.debug("WL: Rereading settings for navitems.")
            settings = self.get_settings(user)
            notify = (self.wsub and settings['notifications'] and settings['display_notify_navitems']) and 'True' or 'False'
            req.session['watchlist_display_notify_navitems'] = notify

        msg = req.session.get('watchlist_message',[])
        if msg:
          add_notice(req, msg)
          del req.session['watchlist_message']
        msg = req.session.get('watchlist_notify_message',[])
        if msg:
          add_notice(req, msg)
          del req.session['watchlist_notify_message']


        href = Href(req.base_path)
        user = req.authname
        if user and user != "anonymous":
            if self.is_watching(realm, resid, user):
                add_ctxtnav(req, _("Unwatch"),
                    href=req.href('watchlist', action='unwatch',
                    resid=resid, realm=realm),
                    title=_("Remove %s from watchlist") % realm)
            else:
                add_ctxtnav(req, _("Watch"),
                    href=req.href('watchlist', action='watch',
                    resid=resid, realm=realm),
                    title=_("Add %s to watchlist") % realm)
            if notify == 'True':
              if self.is_notify(req, realm, resid):
                add_ctxtnav(req, _("Do not Notify me"),
                    href=req.href('watchlist', action='notifyoff',
                    resid=resid, realm=realm),
                    title=_("Do not notify me if %s changes") % realm)
              else:
                add_ctxtnav(req, _("Notify me"),
                    href=req.href('watchlist', action='notifyon',
                    resid=resid, realm=realm),
                    title=_("Notify me if %s changes") % realm)

        return (template, data, content_type)


    def pre_process_request(self, req, handler):
        return handler

    # ITemplateProvider methods:
    def get_htdocs_dirs(self):
        return [('watchlist', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [ resource_filename(__name__, 'templates') ]



class WikiWatchlist(BasicWatchlist):
    realms = ['wiki']
    columns = {'wiki':{
        'name'      : _("Page"),
        'datetime'  : _("Last Changed At"),
        'author'    : _("By"),
        'version'   : _("Version"),
        'diff'      : _("Diff"),
        'history'   : _("History"),
        'unwatch'   : _("U"),
        'notify'    : _("Notify"),
        'comment'   : _("Comment"),
    }}
    default_columns = {'wiki':[
        'name', 'datetime', 'author', 'version', 'diff', 'history', 'unwatch', 'notify', 'comment',
    ]}

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
          if wl.wsub:
            notify = wl.is_notify(req, 'wiki', name)
          wikilist.append({
              'name' : name,
              'author' : '?',
              'datetime' : '?',
              'comment' : tag.strong(_("DELETED!"), class_='deleted'),
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
          if wl.wsub:
            notify = wl.is_notify(req, 'wiki', name)
          t = from_utimestamp( time )
          wikilist.append({
              'name' : name,
              'author' : author,
              'version' : version,
              'datetime' : format_datetime( t, "%F %T %Z" ),
              'timedelta' : pretty_timedelta( t ),
              'timeline_link' : req.href.timeline(precision='seconds',
                  from_=format_datetime ( t, 'iso8601')),
              'comment' : comment,
              'notify'  : notify,
          })
      return wikilist


class TicketWatchlist(BasicWatchlist):
    realms = ['ticket']
    columns = {'ticket':{
        'id'        : _("Ticket"),
        'datetime'  : _("Last Changed At"),
        'author'    : _("By"),
        'changes'   : _("Changes"),
        'commentnum': _("Comment #"),
        'unwatch'   : _("U"),
        'notify'    : _("Notify"),
        'comment'   : _("Comment"),
    }}
    default_columns = {'ticket':[
        'id', 'datetime', 'author', 'changes', 'commentnum', 'unwatch', 'notify', 'comment',
    ]}

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
        SELECT id,type,time,changetime,summary,reporter,status
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
      for id,type,time,changetime,summary,reporter,status in tickets:
          self.commentnum = 0
          self.comment    = ''

          notify = False
          if wl.wsub:
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
                      strng += tag(" ", tag.em(', '.join(added)),
                                   _(" added"))
                  if removed:
                      if added:
                          strng += tag(', ')
                      strng += tag(" ", tag.em(', '.join(removed)),
                                   _(" removed"))
                  return strng
              elif field == 'description':
                  return fieldtag + tag(_(" modified"), " (", tag.a(_("diff"),
                      href=req.href('ticket',id,action='diff',
                      version=self.commentnum)), ")")
              elif field == 'comment':
                  self.commentnum = oldvalue
                  self.comment    = newvalue
                  return tag("")
              elif not oldvalue:
                  return fieldtag + tag(" ", tag.em(newvalue), _(" added"))
              elif not newvalue:
                  return fieldtag + tag(" ", tag.em(oldvalue), _(" deleted"))
              else:
                  return fieldtag + tag(_(" changed from "), tag.em(oldvalue),
                                        _(" to "), tag.em(newvalue))

          changes = []
          author  = reporter
          for author_,field,oldvalue,newvalue in cursor.fetchall():
              author = author_
              changes.extend([format_change(field,oldvalue,newvalue), tag("; ")])
          # changes holds list of formatted changes interleaved with
          # tag('; '). The first change is always the comment which
          # returns an empty tag, so we skip the first two elements
          # [tag(''), tag('; ')] and remove the last tag('; '):
          changes = changes and tag(changes[2:-1]) or tag()
          ct = from_utimestamp( changetime )
          ticketlist.append({
              'id' : to_unicode(id),
              'type' : type,
              'author' : author,
              'commentnum': to_unicode(self.commentnum),
              'comment' : len(self.comment) <= 250 and self.comment or self.comment[:250] + '...',
              'datetime' : format_datetime( ct, "%F %T %Z" ),
              'timedelta' : pretty_timedelta( ct ),
              'timeline_link' : req.href.timeline(precision='seconds',
                  from_=format_datetime ( ct, 'iso8601')),
              'changes' : changes,
              'summary' : summary,
              'status'  : status,
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

