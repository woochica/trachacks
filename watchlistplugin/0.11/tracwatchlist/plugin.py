"""
 Wattchlist Plugin for Trac
 Copyright (c) November 2008  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""
from trac.core import *

from  trac.env         import  IEnvironmentSetupParticipant
from  trac.util        import  format_datetime, pretty_timedelta
from  trac.web.chrome  import  INavigationContributor
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.web.chrome  import  ITemplateProvider, add_ctxtnav, add_link, add_script
from  trac.web.href    import  Href
from  trac.util.text   import  to_unicode
from  genshi.builder   import  tag, Markup
from  urllib           import  quote_plus


class WatchlistError(TracError):
    show_traceback = False
    title = 'Watchlist Error'

    def __init__(self, message):
        Exception.__init__(self, tag.div(message, class_='system-message') )



class WatchlinkPlugin(Component):

    implements( INavigationContributor, IRequestHandler, IRequestFilter,
                IEnvironmentSetupParticipant, ITemplateProvider )

    ### methods for INavigationContributor
    def get_active_navigation_item(self, req):
        if req.path_info.startswith("/watchlist"):
            return 'watchlist'
        return ''

    def get_navigation_items(self, req):
        href = Href(req.base_path)
        user = req.authname
        if user and user != 'anonymous' and self.has_watchlist(user):
            yield ('mainnav', 'watchlist', tag.a( "Watchlist", href=href("watchlist") ) )


    ### methods for IRequestHandler
    def match_request(self, req):
        return req.path_info.startswith("/watchlist")


    def process_request(self, req):
        href = Href(req.base_path)
        user = to_unicode( req.authname )
        if not user or user == 'anonymous':
            raise WatchlistError(
                    tag( "Please ", tag.a("log in", href=href('login')),
                        " to view or change your watchlist!" ) )

        args = req.args
        wldict = args
        if 'action' in args:
            action = args['action']
        else:
            action = 'view'

        if action in ('watch','unwatch'):
            try:
                realm = to_unicode( args['realm'] )
                resid = to_unicode( args['resid']    )
            except KeyError:
                raise WatchlistError("Realm and ResId needed for watch/unwatch action!")
            if realm not in ('wiki','ticket'):
                raise WatchlistError("Only wikis and tickets can be watched/unwatched!")
            is_watching = self.is_watching(realm, resid, user)
            realm_perm  = realm.upper() + '_VIEW' in req.perm
        else:
            is_watching = None

        wlhref = href("watchlist")
        add_ctxtnav(req, "Watched Wikis",   href=wlhref + '#wikis')
        add_ctxtnav(req, "Watched Tickets", href=wlhref + '#tickets')

        wldict['is_watching'] = is_watching
        wiki_perm   = 'WIKI_VIEW'   in req.perm
        ticket_perm = 'TICKET_VIEW' in req.perm
        wldict['wiki_perm']   = wiki_perm
        wldict['ticket_perm'] = ticket_perm

        # DB look-up
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if action == "watch":
            lst = (user, realm, resid)
            if realm_perm and not is_watching:
                # Check if wiki/ticket exists:
                cursor.execute(
                    "SELECT count(*) FROM %s WHERE %s=%%s;" %
                      (realm, realm == 'wiki' and 'name' or 'id'), (resid,) )
                count = cursor.fetchone()
                if not count or not count[0]:
                    raise WatchlistError(
                        "Selected resource %s:%s doesn't exists!" % (realm,resid) )
                cursor.execute(
                    "INSERT INTO watchlist (wluser, realm, resid) "
                    "VALUES (%s,%s,%s);", lst )
                db.commit()
            action = "view"
        elif action == "unwatch":
            lst = (user, realm, resid)
            if realm_perm and is_watching:
                cursor.execute(
                    "DELETE FROM watchlist "
                    "WHERE wluser=%s AND realm=%s AND resid=%s;", lst )
                db.commit()
            action = "view"

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
                    wikilist.append({
                        'name' : name,
                        'author' : '?',
                        'datetime' : '?',
                        'comment' : tag.strong("DELETED!", class_='deleted'),
                        'deleted' : True,
                    })
                # Existing watched wikis:
                cursor.execute(
                    "SELECT name,author,time,MAX(version),comment FROM %s WHERE name IN "
                    "(SELECT resid FROM watchlist WHERE wluser=%%s AND realm=%%s) "
                    "GROUP BY name ORDER BY time DESC;" % realm, (user,realm) )
                for name,author,time,version,comment in cursor.fetchall():
                    wikilist.append({
                        'name' : name,
                        'author' : author,
                        'version' : version,
                        'datetime' : format_datetime( time ),
                        'timedelta' : pretty_timedelta( time ),
                        'timeline_link' : timeline_link( time ),
                        'comment' : comment,
                    })
                wldict['wikilist'] = wikilist


            if ticket_perm:
                ticketlist = []
                cursor.execute(
                    "SELECT id,type,time,changetime,summary,reporter FROM ticket WHERE id IN "
                    "(SELECT CAST(resid AS int) FROM watchlist WHERE wluser=%s AND realm='ticket') "
                    "GROUP BY id,type,time,changetime,summary,reporter "
                    "ORDER BY changetime DESC;", (user,) )
                tickets = cursor.fetchall()
                for id,type,time,changetime,summary,reporter in tickets:
                    self.commentnum = 0
                    self.comment    = ''
                    cursor.execute(
                        "SELECT author,field,oldvalue,newvalue FROM ticket_change "
                        "WHERE ticket=%s and time=%s "
                        "ORDER BY field=='comment' DESC;",
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
                               href=href('ticket',id,action='diff',version=commentnum)), ")")
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
            if not self.is_watching(realm, resid, user):
                add_ctxtnav(req, "Watch", href=href('watchlist', action='watch',
                    resid=resid, realm=realm), title="Add %s to watchlist" % realm)
            else:
                add_ctxtnav(req, "Unwatch", href=href('watchlist', action='unwatch',
                    resid=resid, realm=realm), title="Remove %s from watchlist" % realm)
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
    def _create_db_table(self, db=None):
        """ Create DB table if it not exists. """
        from trac.db import Table, Column, Index, DatabaseManager
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        table = Table('watchlist')[
                    Column('wluser'),
                    Column('realm'),
                    Column('resid') ]

        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

        # Set database schema version.
        try:
            cursor.execute("INSERT INTO system (name, value) VALUES"
              " ('watchlist_version', '1')")
        except:
            pass
        return


    def _update_db_table(self, db=None):
        """ Update DB table. """
        self.env.log.debug("Updating DB table.")

        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute(
                "ALTER TABLE watchlist RENAME COLUMN user TO wluser;")
            cursor.execute(
                "ALTER TABLE watchlist RENAME COLUMN id   TO resid;")
        except Exception, e:
            raise TracError("Couldn't rename DB table columns: " + to_unicode(e))
        try:
            cursor.execute("INSERT INTO system (name, value) VALUES"
              " ('watchlist_version', '1')")
        except:
            pass
        return

    def environment_created(self):
        self._create_db_table()
        return

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(wluser),count(resid),count(realm) FROM watchlist;")
            count = cursor.fetchone()
            if count is None:
                return True
            cursor.execute("SELECT value FROM system WHERE name='watchlist_version';")
            (version,) = cursor.fetchone()
            if not version or int(version) < 1:
                return True
        except:
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM watchlist;")
        except:
            self._create_db_table(db)
        else:
            try:
                cursor.execute("SELECT count(user),count(id),count(realm) FROM watchlist;")
            except:
                pass
            else:
                self._update_db_table(db)
        return

