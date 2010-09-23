# -*- coding: utf-8 -*-
"""
 Wattchlist Plugin for Trac
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
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

from trac.core import *

from  trac.env         import  IEnvironmentSetupParticipant
from  trac.util        import  format_datetime, pretty_timedelta
from  trac.web.chrome  import  INavigationContributor
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.web.chrome  import  ITemplateProvider, add_ctxtnav, add_link, add_script, add_notice
from  trac.web.href    import  Href
from  trac.util.text   import  to_unicode
from  genshi.builder   import  tag, Markup
from  urllib           import  quote_plus
from  trac.config      import  BoolOption
from  trac.db          import  Table, Column, Index, DatabaseManager
from  trac.wiki.model  import  WikiPage
from  trac.ticket.model import Ticket

__DB_VERSION__ = 3

class WatchlistError(TracError):
    show_traceback = False
    title = 'Watchlist Error'


class WatchlistPlugin(Component):
    """For documentation see http://trac-hacks.org/wiki/WatchlistPlugin"""

    implements( INavigationContributor, IRequestHandler, IRequestFilter,
                IEnvironmentSetupParticipant, ITemplateProvider )
    gnotify = BoolOption('watchlist', 'notifications', False,
                "Enables notification features")
    gnotifyctxtnav = BoolOption('watchlist', 'display_notify_navitems', False,
                "Enables notification navigation items")
    gnotifycolumn = BoolOption('watchlist', 'display_notify_column', True,
                "Enables notification column in watchlist tables")
    gnotifybydefault = BoolOption('watchlist', 'notify_by_default', False,
                "Enables notifications by default for all watchlist entries")
    gredirectback = BoolOption('watchlist', 'stay_at_resource', False,
                "The user stays at the resource after a watch/unwatch operation "
                "and the watchlist page is not displayed.")
    gmsgrespage = BoolOption('watchlist', 'show_messages_on_resource_page', True, 
                "Enables action messages on resource pages.")
    gmsgwlpage  = BoolOption('watchlist', 'show_messages_on_watchlist_page', True, 
                "Enables action messages when going to the watchlist page.")
    gmsgwowlpage = BoolOption('watchlist', 'show_messages_while_on_watchlist_page', True, 
                "Enables action messages while on watchlist page.")


    if gnotify:
      try:
        # Import methods from WatchSubscriber from the AnnouncerPlugin
        from  announcerplugin.subscribers.watchers  import  WatchSubscriber
        is_notify    = WatchSubscriber.__dict__['is_watching']
        set_notify   = WatchSubscriber.__dict__['set_watch']
        unset_notify = WatchSubscriber.__dict__['set_unwatch']
        set_unwatch  = unset_notify
      except:
        gnotify = False

    # Per user setting # FTTB FIXME
    notifyctxtnav = gnotifyctxtnav

    ### methods for INavigationContributor
    def get_active_navigation_item(self, req):
        if req.path_info.startswith("/watchlist"):
            return 'watchlist'
        return ''

    def get_navigation_items(self, req):
        user = req.authname
        if user and user != 'anonymous':
            yield ('mainnav', 'watchlist', tag.a( "Watchlist", href=req.href("watchlist") ) )

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

        cursor.execute( """
          SELECT count(*) FROM watchlist_settings WHERE wluser=%s LIMIT 0,1""", (user,) )
        ex = cursor.fetchone()
        if not ex or not int(ex[0]):
          cursor.execute(
              "INSERT INTO watchlist_settings VALUES (%s,%s)",
              (user, settingsstr) )
        else:
          cursor.execute(
              "UPDATE watchlist_settings SET settings=%s WHERE wluser=%s ",
              (settingsstr, user) )

        db.commit()
        return True

    def _get_user_settings(self, user):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT settings FROM watchlist_settings WHERE wluser = %s",
            (user,) )

        try:
          (settingsstr,) = cursor.fetchone()
          return dict([ kv.split('=') for kv in settingsstr.split("&") ])
        except:
          return dict()


    def process_request(self, req):
        href = req.href
        user = to_unicode( req.authname )
        if not user or user == 'anonymous':
            raise WatchlistError(
                    tag( "Please ", tag.a("log in", href=href('login')),
                        " to view or change your watchlist!" ) )

        args = req.args
        wldict = args.copy()
        action = args.get('action','view')
        redirectback = self.gredirectback
        ispattern = False# Disabled for now, not implemented fully # args.get('ispattern','0')
        onwatchlistpage = req.environ.get('HTTP_REFERER','').find(href.watchlist()) != -1

        if ispattern or onwatchlistpage:
          redirectback = False

        if action in ('watch','unwatch','notifyon','notifyoff'):
            try:
                realm = to_unicode( args['realm'] )
                resid = to_unicode( args['resid'] )
            except KeyError:
                raise WatchlistError("Realm and ResId needed for watch/unwatch action!")
            if realm not in ('wiki','ticket'):
                raise WatchlistError("Only wikis and tickets can be watched/unwatched!")
            is_watching = self.is_watching(realm, resid, user)
            realm_perm  = realm.upper() + '_VIEW' in req.perm
            if ispattern:
              pattern = self._convert_pattern(resid)
            else:
              reslink = href(realm,resid)
              res_exists  = self.res_exists(realm, resid, user)
        else:
            is_watching = None

        wlhref = href("watchlist")
        add_ctxtnav(req, "Watched Wikis",   href=wlhref + '#wikis')
        add_ctxtnav(req, "Watched Tickets", href=wlhref + '#tickets')
        #add_ctxtnav(req, "Settings", href=wlhref + '#settings')

        wiki_perm   = 'WIKI_VIEW'   in req.perm
        ticket_perm = 'TICKET_VIEW' in req.perm
        wldict['wiki_perm']   = wiki_perm
        wldict['ticket_perm'] = ticket_perm
        wldict['error'] = False
        gnotify = self.gnotify
        wldict['notify'] = gnotify and self.gnotifycolumn
        if onwatchlistpage:
          wldict['show_messages'] = self.gmsgwowlpage
        else:
          wldict['show_messages'] = self.gmsgwlpage
        msgrespage = self.gmsgrespage

        # DB look-up
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if action == "watch":
            lst = (user, realm, resid)
            if realm_perm and not is_watching:
              col =  realm == 'wiki' and 'name' or 'id'
              if ispattern:
                #cursor.log = self.env.log
                # Check if wiki/ticket exists:
                cursor.execute(
                    "SELECT count(*) FROM %s WHERE %s LIKE %%s" % (realm,col), (pattern,) )
                    #("'"+pattern+"'",) )
                count = cursor.fetchone()
                if not count or not count[0]:
                    raise WatchlistError(
                        "Selected pattern %s:%s (%s) doesn't match anything!" % (realm,resid,pattern) )
                #cursor.execute(
                #    "INSERT INTO watchlist (wluser, realm, resid) "
                #    "SELECT '%s','%s',%s FROM %s WHERE %s LIKE %%s" % (user,realm,col,
                #      realm,col), (resid,) )
                cursor.execute(
                    "INSERT INTO watchlist (wluser, realm, resid) " +
                    "SELECT %s,%s,%s FROM %s WHERE %s LIKE %%s" % \
                    ("'"+user+"'","'"+realm+"'", col, realm, col), (pattern,) )
              else:
                if not res_exists:
                    wldict['error'] = True
                    if redirectback and not onwatchlistpage:
                      raise WatchlistError(
                          "Selected resource %s:%s doesn't exists!" % (realm,resid) )
                    redirectback = False
                else:
                    cursor.execute(
                        "INSERT INTO watchlist (wluser, realm, resid) "
                        "VALUES (%s,%s,%s);", lst )
              db.commit()
            if not onwatchlistpage and redirectback and msgrespage:
                  req.session['watchlist_message'] = (
                    'This %s has been added to your watchlist.' % realm)
            if self.gnotify and self.gnotifybydefault:
              action = "notifyon"
            else:
              if redirectback:
                req.redirect(reslink)
                raise RequestDone
              action = "view"
        elif action == "unwatch":
            lst = (user, realm, resid)
            if realm_perm:
              if ispattern:
                #cursor.log = self.env.log
                is_watching = True
                cursor.execute(
                    "DELETE FROM watchlist "
                    "WHERE wluser=%s AND realm=%s AND resid LIKE %s", (user,realm,pattern) )
                db.commit()
              elif is_watching:
                cursor.execute(
                    "DELETE FROM watchlist "
                    "WHERE wluser=%s AND realm=%s AND resid=%s;", lst )
                db.commit()
              elif not res_exists:
                wldict['error'] = True
                if redirectback and not onwatchlistpage:
                  raise WatchlistError(
                      "Selected resource %s:%s doesn't exists!" % (realm,resid) )
                redirectback = False
            if not onwatchlistpage and redirectback and msgrespage:
              req.session['watchlist_message'] = (
                'This %s has been removed from your watchlist.' % realm)
            if self.gnotify and self.gnotifybydefault:
              action = "notifyoff"
            else:
              if redirectback:
                req.redirect(reslink)
                raise RequestDone
              action = "view"

        if action == "notifyon":
            if self.gnotify:
              self.set_notify(req.session.sid, True, realm, resid)
              db.commit()
            if redirectback:
              if msgrespage:
                req.session['watchlist_notify_message'] = (
                  'You are now receiving '
                  'change notifications about this resource.')
              req.redirect(reslink)
              raise RequestDone
            action = "view"
        elif action == "notifyoff":
            if self.gnotify:
              self.unset_notify(req.session.sid, True, realm, resid)
              db.commit()
            if redirectback:
              if msgrespage:
                req.session['watchlist_notify_message'] = (
                  'You are no longer receiving '
                  'change notifications about this resource.')
              req.redirect(reslink)
              raise RequestDone
            action = "view"

        if action == "settings":
          d = args.copy()
          del d['action']
          self._save_user_settings(user, d)
          action = "view"
          wldict['user_settings'] = d
        else:
          wldict['user_settings'] = self._get_user_settings(user)

        wldict['is_watching'] = is_watching
        if action == "view":
            timeline = href('timeline', precision='seconds') + "&from="
            def timeline_link(time):
                return timeline + quote_plus( format_datetime (time,'iso8601') )

            wikilist = []
            if wiki_perm:
                # Watched wikis which got deleted:
                cursor.execute(
                    "SELECT resid FROM watchlist WHERE realm='wiki' AND wluser=%s "
                    "AND resid NOT IN (SELECT DISTINCT name FROM wiki);", (user,) )

                for (name,) in cursor.fetchall():
                    notify = False
                    if gnotify:
                      notify = self.is_notify(req.session.sid, True, 'wiki', name)
                    wikilist.append({
                        'name' : name,
                        'author' : '?',
                        'datetime' : '?',
                        'comment' : tag.strong("DELETED!", class_='deleted'),
                        'notify'  : notify,
                        'deleted' : True,
                    })
                # Existing watched wikis:
                cursor.execute(
                    "SELECT name,author,time,version,comment FROM wiki AS w1 WHERE name IN "
                    "(SELECT resid FROM watchlist WHERE wluser=%s AND realm='wiki') "
                    "AND version=(SELECT MAX(version) FROM wiki AS w2 WHERE w1.name=w2.name) "
                    "ORDER BY time DESC;", (user,) )

                wikis = cursor.fetchall()
                for name,author,time,version,comment in wikis:
                    notify = False
                    if gnotify:
                      notify = self.is_notify(req.session.sid, True, 'wiki', name)
                    wikilist.append({
                        'name' : name,
                        'author' : author,
                        'version' : version,
                        'datetime' : format_datetime( time ),
                        'timedelta' : pretty_timedelta( time ),
                        'timeline_link' : timeline_link( time ),
                        'comment' : comment,
                        'notify'  : notify,
                    })
                wldict['wikilist'] = wikilist


            if ticket_perm:
                ticketlist = []
                cursor.execute(
                    "SELECT id,type,time,changetime,summary,reporter FROM ticket WHERE id IN "
                    "(SELECT CAST(resid AS decimal) FROM watchlist WHERE wluser=%s AND realm='ticket') "
                    "GROUP BY id,type,time,changetime,summary,reporter "
                    "ORDER BY changetime DESC;", (user,) )
                tickets = cursor.fetchall()
                for id,type,time,changetime,summary,reporter in tickets:
                    self.commentnum = 0
                    self.comment    = ''

                    notify = False
                    if gnotify:
                      notify = self.is_notify(req.session.sid, True, 'ticket', id)

                    cursor.execute(
                        "SELECT author,field,oldvalue,newvalue FROM ticket_change "
                        "WHERE ticket=%s and time=%s "
                        "ORDER BY field DESC;",
                        (id, changetime )
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
                               href=href('ticket',id,action='diff',version=self.commentnum)), ")")
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
                        'datetime' : format_datetime( changetime ),
                        'timedelta' : pretty_timedelta( changetime ),
                        'timeline_link' : timeline_link( changetime ),
                        'changes' : changes,
                        'summary' : summary,
                        'notify'  : notify,
                    })
                    wldict['ticketlist'] = ticketlist
            return ("watchlist.html", wldict, "text/html")
        else:
            raise WatchlistError("Invalid watchlist action '%s'!" % action)

        raise WatchlistError("Watchlist: Unsupported request!")

    def has_watchlist(self, user):
        """Checks if user has a non-empty watchlist."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT count(*) FROM watchlist WHERE wluser=%s;", (user,)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True

    def res_exists(self, realm, resid, user):
        """Checks if resource exists """
        if realm == 'wiki':
          res_exists = WikiPage(self.env, resid).exists
        else:
          try:
            res_exists = Ticket(self.env, resid).exists
          except:
            res_exists = False
        return res_exists

    def is_watching(self, realm, resid, user):
        """Checks if user watches the given element."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT count(*) FROM watchlist WHERE realm=%s and resid=%s "
            "and wluser=%s;", (realm, to_unicode(resid), user)
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

        if realm not in ('wiki','ticket') \
          or realm.upper() + '_VIEW' not in req.perm:
            return (template, data, content_type)

        href = Href(req.base_path)
        user = req.authname
        if user and user != "anonymous":
            if self.is_watching(realm, resid, user):
                add_ctxtnav(req, "Unwatch", href=href('watchlist', action='unwatch',
                    resid=resid, realm=realm), title="Remove %s from watchlist" % realm)
            else:
                add_ctxtnav(req, "Watch", href=href('watchlist', action='watch',
                    resid=resid, realm=realm), title="Add %s to watchlist" % realm)
            if self.gnotify and self.notifyctxtnav:
              if self.is_notify(req.session.sid, True, realm, resid):
                add_ctxtnav(req, "Do not Notify me", href=href('watchlist', action='notifyoff',
                    resid=resid, realm=realm), title="No not notify me if %s changes" % realm)
              else:
                add_ctxtnav(req, "Notify me", href=href('watchlist', action='notifyon',
                    resid=resid, realm=realm), title="Notify me if %s changes" % realm)

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


    # IEnvironmentSetupParticipant methods:
    def _create_db_table(self, db=None, name='watchlist'):
        """ Create DB table if it not exists. """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.log = self.env.log
        self.env.log.info("Creating table '%s' for WatchlistPlugin" % name )
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        table = Table(name)[
                    Column('wluser'),
                    Column('realm'),
                    Column('resid'),
                ]

        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

        return

    def _create_db_table2(self, db=None):
        """ Create settings DB table if it not exists. """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.log = self.env.log
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.env.log.info("Creating 'watchlist_settings' table")

        table = Table('watchlist_settings', key=['wluser',])[
                    Column('wluser'),
                    Column('settings'),
                ]

        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

        return

    def environment_created(self):
        self._create_db_table()
        return


    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(wluser),count(resid),count(realm) FROM watchlist")
            count = cursor.fetchone()
            if count is None:
                self.env.log.info("Watchlist table format to old")
                return True
            cursor.execute("SELECT count(*) FROM watchlist_settings")
            count = cursor.fetchone()
            if count is None:
                self.env.log.info("Watchlist settings table not found")
                return True
            cursor.execute("SELECT value FROM system WHERE name='watchlist_version'")
            version = cursor.fetchone()
            if not version or int(version[0]) < __DB_VERSION__:
                self.env.log.info("Watchlist table version to old")
                return True
        except Exception, e:
            cursor.connection.rollback()
            self.env.log.info("Watchlist table needs to be upgraded: " + unicode(e))
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        version = 0
        # Ensure system entry exists:
        try:
          cursor.execute("SELECT value FROM system WHERE name='watchlist_version'")
          version = cursor.fetchone()
          if not version:
            raise Exception("No version entry in system table")
          version = int(version[0])
        except Exception, e:
          self.env.log.info("Creating system table entry for watchlist plugin: " + unicode(e))
          cursor.connection.rollback()
          version = 0

        try:
            cursor.execute("SELECT count(*) FROM watchlist")
        except:
            self.env.log.info("No previous watchlist table found")
            self._create_db_table(db)
            self._create_db_table2(db)
            cursor = db.cursor()
            cursor.execute("DELETE FROM system WHERE "
                           "name='watchlist_version'" )
            cursor.execute("INSERT INTO system (name,value) "
                           "VALUES ('watchlist_version',%s) ", (str(__DB_VERSION__),) )
            return

        try:
            cursor.execute("SELECT count(*) FROM watchlist_settings")
        except:
            self.env.log.info("No previous watchlist_settings table found")
            cursor.connection.rollback()
            self._create_db_table2(db)

        # Upgrade existing database
        self.env.log.info("Updating watchlist table")
        try:
            self.env.log.info("Old version: %d, new version: %d" % (int(version),int(__DB_VERSION__)))
        except:
            pass

        try:
            try:
              cursor.execute("DROP TABLE watchlist_new")
            except:
              pass #cursor.connection.rollback()
            self._create_db_table(db, 'watchlist_new')
            cursor = db.cursor()
            cursor.log = self.log
            try: # from version 0
              cursor.execute("INSERT INTO watchlist_new (wluser, realm, resid) "
                             "SELECT user, realm, id FROM watchlist")
              self.env.log.info("Update from version 0")
            except: # from version 1
              self.env.log.info("Update from version 1")
              cursor.connection.rollback ()
              cursor = db.cursor()
              cursor.execute("INSERT INTO watchlist_new (wluser, realm, resid) "
                              "SELECT wluser, realm, resid FROM watchlist")

            self.env.log.info("Moving new table to old one")
            cursor.execute("DROP TABLE watchlist")
            cursor.execute("ALTER TABLE watchlist_new RENAME TO watchlist")
            cursor.execute("DELETE FROM system WHERE "
                           "name='watchlist_version'" )
            cursor.execute("INSERT INTO system (name,value) "
                           "VALUES ('watchlist_version',%s) ", (str(__DB_VERSION__),) )
        except Exception, e:
            cursor.connection.rollback ()
            self.env.log.info("Couldn't update DB: " + to_unicode(e))
            raise TracError("Couldn't update DB: " + to_unicode(e))
        return

