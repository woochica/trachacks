"""
    Description:
    ------------
    This script adds the necessary entries to the private_comment table
    to enable the editing of comments which were created before the
    installation of the PrivateCommentsPlugin.

    Usage:
    ------
    Place this file into your Trac context and run it on the command line

    Notes:
    ------
    - Only works for SQLite databases
"""

import sys
import sqlite3

sqlite_database = 'db/trac.db'


def getTicketChanges(conn):
    c = conn.cursor()
    c.execute('SELECT ticket, oldvalue FROM ticket_change')

    ticket_changes = []
    for row in c:
        find = row[1].find('.')
        if find == -1:
            comment_id = row[1]
        else:
            comment_id = row[1][find+1:]

        try:
            comment_id = int(comment_id)
        except:
            continue

        ticket_changes.append((row[0], comment_id))

    c.close()

    return ticket_changes


def existsPrivateComment(conn, ticket_id, comment_id):
    c = conn.cursor()
    try:
        c.execute("""
            SELECT private FROM private_comment
            WHERE ticket_id=:ticket_id AND comment_id=:comment_id
            """, (ticket_id, comment_id))
        private = c.fetchone()
        c.close()

        if private is None:
            return False

        return True
    except:
        c.close()
        return False


def createPrivateComment(conn, ticket_id, comment_id, private):
    c = conn.cursor()
    c.execute("""
        INSERT INTO private_comment (ticket_id,comment_id,private)
        VALUES (:ticket_id,:comment_id,:private)
        """, (int(ticket_id), int(comment_id), int(private)))
    c.close()


def main(argv):
    conn = sqlite3.connect(sqlite_database)
    ticket_changes = getTicketChanges(conn)

    for ticket_change in ticket_changes:
        if not existsPrivateComment(conn, ticket_change[0], ticket_change[1]):
            createPrivateComment(conn, ticket_change[0], ticket_change[1], 0)
            print repr(ticket_change)+' -> Created entry!'
        else:
            print repr(ticket_change)+' -> Exists already!'

    conn.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
