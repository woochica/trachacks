from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.util.datefmt import format_datetime

__all__ = ['StatsMacro']

class StatsMacro(Component):
    """A macro to generate user wiki user statistics.
    Shows pages added and edited, images added, and first and last edit.
    Stats for an individual:
    {{{
    [[Stats(Username)]]
    }}}
    Stats for the entire wiki:
    {{{
    [[Stats]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Stats'

    def get_images(self, username):
        """ Return a dictionary indexed by username with count
        of images added.  If username is None, all users are returned.
        If username is provided, None is returned if a user has no images."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = '''SELECT author, count(*)
                FROM attachment '''
        if username:
            sql += 'WHERE author = "%s" '%username

        sql += ' GROUP BY author'
        
        cursor.execute(sql)

        rows= cursor.fetchall()
        ret = {}
        for i in rows:
            ret[i[0]] = i[1]
            
        return ret                       

    def get_stats(self, username):
        """ Return a list of user, pages_created, pages_edited, first_edit
        last_edit.  If username is none, list contains all users in
        the wiki."""
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = '''SELECT
                author,
                SUM(IF(version = 1, 1, 0)) as pages_created,
                SUM(IF(version = 1, 0, 1)) as pages_edited,
                MIN(time) as first_edit,
                MAX(time) as last_edit
                FROM wiki '''
        if username:
            sql = sql+'WHERE author = "%s" '%username

        sql += ' GROUP BY author ORDER BY pages_created desc'

        cursor.execute(sql)

        rows = cursor.fetchall()
        return rows                       

    def expand_macro(self, formatter, name, txt):

        if txt:
            username = txt.strip('"')
            out = "<h3>%s's Statistics</h3>"%username
        else:
            username = None
            out = '<h3>User Statistics</h3>'

        rows = self.get_stats(username)
        images = self.get_images(username)

        if rows is None:
            return 'Error with query'
        
        out += '<table class="wiki"><tr>'
        
        # missing usernname -> we're doing all users, so add a user column
        if username is None:
            out += '<th>User</th>'
            
        out += '<th>Edits</th><th>Pages Created</th><th>Images Contributed</th><th>First Edit</th><th>Most Recent Edit</th></tr>'

        for row in rows:
            out += '<tr>'
            if username is None:
                out += '<td>%s</td>'%row[0]
            out += '<td>%s</td><td>%s</td>'%(row[1],row[2])
            if images is not None and images.has_key(row[0]):
                image_count = images[row[0]]
            else:
                image_count = 0
            out += '<td>%d</td>'%image_count
            out += '<td>%s</td><td>%s</td></tr>'\
                   %(format_datetime(row[3]),format_datetime(row[4]))

        out += '</table>'

        return out
