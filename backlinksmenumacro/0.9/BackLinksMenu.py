#
# BackLinksMenu plugin for Trac 1.0
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
#
#
from StringIO import StringIO
import string

def execute(hdf, args, env):
    db = env.get_db_cnx()
    cursor = db.cursor()

    thispage = None

    if args:
        thispage = args.replace('\'', '\'\'')
    else:
	thispage = hdf.getValue('wiki.page_name', '')

    sql = 'SELECT w1.name FROM wiki w1, ' + \
          '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
          'WHERE w1.version = w2.version AND w1.name = w2.name '

    if thispage:
	    sql += 'AND (w1.text LIKE \'%%[wiki:%s %%\' ' % (unicode(thispage, "utf-8").encode ("utf-8"))
	    sql += 'OR w1.text LIKE \'%%[wiki:%s]%%\')' % (unicode (thispage, "utf-8").encode ("utf-8"))
	    #sql += 'AND w1.text LIKE \'%%[wiki:%s %%\' ' % thispage

    cursor.execute(sql)

    buf = StringIO()
    buf.write('<div class="wiki-toc">')
    buf.write('Pages linking to %s:<br />\n' % (unicode (thispage, "utf-8")))

    while 1:
        row = cursor.fetchone()
        if row == None:
            break
	s2 = unicode (thispage, "utf-8")
        if row[0] == s2:
	    pass
        else:
            buf.write('<a href="%s">' % env.href.wiki(row[0]))
            buf.write(row[0])
            buf.write('</a><br />\n')


    buf.write('</div>')

    return buf.getvalue()
