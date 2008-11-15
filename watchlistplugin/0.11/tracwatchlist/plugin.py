"""
nav:
a plugin for Trac
http://trac.edgewall.org
"""

from trac.core import *

from  trac.env         import  IEnvironmentSetupParticipant
from  trac.util        import  format_datetime, pretty_timedelta
from  trac.web.chrome  import  INavigationContributor
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.web.chrome  import  ITemplateProvider, add_ctxtnav, add_link, add_script
from  trac.web.href    import  Href
from  genshi.builder   import  tag, Markup
from  urllib           import  quote_plus

class nav(Component):

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

        user = req.authname
        if not user or user == 'anonymous':
            raise TracError("Please log in to view or change your watchlist!")

        args = req.args
        wldict = args
        if 'action' in args:
            action = args['action']
        else:
            action = 'view'

        if action in ('watch','unwatch'):
            try:
                realm = args['realm']
                id    = args['id']
            except KeyError:
                raise TracError("Realm and Id needed for watch/unwatch action!")
            is_watching = self.is_watching(realm, id, user)
        else:
            is_watching = None

        href = Href(req.base_path)("watchlist")
        add_ctxtnav(req, "Watched Wikis", href=href + '#wikis')
        add_ctxtnav(req, "Watched Tickets", href=href + '#tickets')

        wldict['is_watching'] = is_watching

        wiki_perm   = 'WIKI_VIEW'   in req.perm
        ticket_perm = 'TICKET_VIEW' in req.perm
        wldict['wiki_perm']   = wiki_perm
        wldict['ticket_perm'] = ticket_perm

        # DB look-up
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if action == "watch":
            lst = (user, realm, id)
            if not is_watching:
                cursor.execute(
                    "INSERT INTO watchlist (user, realm, id) "
                    "VALUES ('%s','%s','%s');" % lst
                )
                db.commit()
            action = "view"
        elif action == "unwatch":
            lst = (user, realm, id)
            if is_watching:
                cursor.execute(
                    "DELETE FROM watchlist "
                    "WHERE user='%s' AND realm='%s' AND id='%s';"
                     % lst
                )
                db.commit()
            action = "view"

        if action == "view":
            href = Href(req.base_path)
            timeline = href('timeline', precision='seconds') + "&from="
            def timeline_link(time):
                return timeline + quote_plus( format_datetime (time,'iso8601') )

            wikilist = []
            if wiki_perm:
                cursor.execute(
                    "SELECT name,author,time,MAX(version),comment FROM %(realm)s WHERE name IN "
                    "(SELECT id FROM watchlist WHERE user='%(user)s' AND realm='%(realm)s') "
                    "GROUP BY name ORDER BY time DESC;" % { 'user':user, 'realm':'wiki' }
                )
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


            def format_change(field,oldvalue,newvalue):
                """Formats tickets changes."""
                fieldstr = "<strong>%s</strong> " % field
                if field == 'cc':
                    oldvalues = set(oldvalue and oldvalue.split(', ') or [])
                    newvalues = set(newvalue and newvalue.split(', ') or [])
                    added   = newvalues.difference(oldvalues)
                    removed = oldvalues.difference(newvalues)
                    str = fieldstr
                    if added:
                        str += "<em>%s</em> added" % ', '.join(added)
                    if removed:
                        if added:
                            str += ', '
                        str += "<em>%s</em> removed" % ', '.join(removed)
                    return str
                elif not oldvalue:
                    return fieldstr + "<em>%s</em> added" % newvalue
                elif not newvalue:
                    return fieldstr + "<em>%s</em> deleted" % oldvalue
                else:
                    return fieldstr + "changed from <em>%s</em> to <em>%s</em>"\
                              % (oldvalue, newvalue)

            if ticket_perm:
                ticketlist = []
                cursor.execute(
                    "SELECT id,type,time,changetime,summary,reporter FROM %(realm)s WHERE id IN "
                    "(SELECT id FROM watchlist WHERE user='%(user)s' AND realm='%(realm)s') "
                    "GROUP BY id ORDER BY changetime DESC;" % { 'user':user, 'realm':'ticket' }
                )
                tickets = cursor.fetchall()
                for id,type,time,changetime,summary,reporter in tickets:
                    cursor.execute(
                        "SELECT author,field,oldvalue,newvalue FROM ticket_change "
                        "WHERE ticket='%s' and time='%s' ORDER BY field;"
                         % (id, changetime )
                    )
                    changes = []
                    author  = reporter
                    for author_,field,oldvalue,newvalue in cursor.fetchall():
                        author = author_
                        changes.append( format_change(field,oldvalue,newvalue) )
                    changes = Markup('; '.join(changes))
                    cursor.execute(
                        "SELECT count(DISTINCT time) FROM ticket_change WHERE ticket='%s';"
                         % (id)
                    )
                    (commentnum,) = cursor.fetchone()
                    ticketlist.append({
                        'id' : str(id),
                        'type' : type,
                        'author' : author,
                        'commentnum': str(commentnum),
                        'datetime' : format_datetime( changetime ),
                        'timedelta' : pretty_timedelta( changetime ),
                        'timeline_link' : timeline_link( changetime ),
                        'changes' : changes,
                        'summary' : summary,
                    })
                    wldict['ticketlist'] = ticketlist
            return ("watchlist.html", wldict, "text/html")
        else:
            raise TracError("Invalid watchlist action '%s'!" % action)

        raise TracError("Watchlist: Unsupported request!")

    def has_watchlist(self, user):
        """Checks if user has a non-empty watchlist."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT count(*) FROM watchlist WHERE user='%s';" % (user)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True

    def is_watching(self, realm, id, user):
        """Checks if user watches the given element."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT count(*) FROM watchlist WHERE realm='%s' and id='%s' and user='%s';"
             % (realm, id, user)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True

    ### methods for IRequestFilter
    def post_process_request(self, req, template, data, content_type):
        # Extract realm and id from path:
        parts = req.path_info[1:].split('/',2)


        # Handle special case for '/' and '/wiki'
        if len(parts) == 0 or not parts[0]:
            parts = ["wiki", "WikiStart"]
        elif len(parts) == 1:
            parts.append("WikiStart")

        realm, id = parts[:2]

        if realm not in ('wiki','ticket') \
          or realm.upper() + '_VIEW' not in req.perm:
            return (template, data, content_type)

        href = Href(req.base_path)
        user = req.authname
        if user and user != "anonymous":
            if not self.is_watching(realm, id, user):
                add_ctxtnav(req, "Watch", href=href('watchlist', action='watch',
                    id=id, realm=realm), title="Add %s to watchlist" % realm)
            else:
                add_ctxtnav(req, "Unwatch", href=href('watchlist', action='unwatch',
                    id=id, realm=realm), title="Remove %s from watchlist" % realm)
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
        self.env.log.debug("Creating DB table (if not already exists).")

        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user  text,
                realm text,
                id    text
            );""")
        return

    def environment_created(self):
        self._create_db_table()
        return

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM watchlist;")
            count = cursor.fetchone()
            if count is None:
                return True
        except:
            return True
        return False

    def upgrade_environment(self, db):
        self._create_db_table(db)
        return

