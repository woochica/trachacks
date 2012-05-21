#!/usr/bin/env python

# Inserts missing changeset comments in the corresponding ticket(s).

import os
import re
import sys
import subprocess
import sqlite3
from optparse import OptionParser

def get_repos(conn):
    """Return a dict of hg repo id:name. svn repos are omitted."""
    repos = {}
    c = conn.cursor()
    c.execute("select id, value from repository where name='name' " + \
              " and id not in " + \
              "  (select id from repository where name='repository_dir');")
    for id, name in c:
        repos[id] = name
    return repos

def get_reponame(conn, repo, repos_dir, repos, rev, counts):
    for num,reponame in repos.items():
        dir = os.path.join(repos_dir, reponame)
        if not os.path.exists(dir):
            continue
        os.chdir(dir)
        if subprocess.call("hg log -r %s" % rev, shell=True) == 0: # success
            if repos[repo] != reponame:
                c = conn.cursor()
                c.execute("update revision set repos=? where rev=?;", (num,rev,))
                conn.commit()
            return reponame
        counts['wrongrepo'] += 1
        print ',',
    raise Exception("rev %s not found in any hg repos" % rev)

def exists(conn, ticket, time_, author):
    c = conn.cursor()
    c.execute("select count(*) from ticket_change "+ \
              "where ticket=? and time=? and author=? and field='comment';",
              (ticket, time_, author))
    for (count,) in c: pass
    return count > 0

def main(dbfile, repos_dir):
    counts = {'inserts':0, 'svnrepo':0, 'wrongrepo':0, 'exists':0}
    ticketref_re = re.compile(r"(addresses|ref|refs|references|see|merges) #([0-9]+)")
    
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    # cache reponames
    repos = get_repos(conn)
    repo_counts = {}
    for reponame in repos.values():
        repo_counts[reponame] = 0
    
    # iterate through each revision
    c.execute("select repos, rev, time, author, message from revision;")
    for repo, rev, time_, author, message in c:
        # skip svn repos
        if repo not in repos:
            counts['svnrepo'] += 1
            print '.',
            continue
        
        for _,ticket in ticketref_re.findall(message):
            # check if changeset comment already exists
            if exists(conn, ticket, time_, author):
                counts['exists'] += 1
                print '-',
                continue
            
            # find correct repos
            # .. and correct the repos num in revision table!
            reponame = get_reponame(conn, repo, repos_dir, repos, rev, counts)
            repo_counts[reponame] += 1
            
            # insert changeset
            insert_ticket_comment(conn, ticket, time_, author,
                                  reponame, rev, message)
            counts['inserts'] += 1
            print '+',
            
    conn.close()
    print
    print counts
    print repo_counts

def insert_ticket_comment(conn, ticket, time_, author, reponame, rev, message):
    """Create the ticket comment from the changeset data."""
    revstring = rev + '/' + reponame
    comment = """\
In [%s]:
{{{
#!CommitTicketReference repository="%s" revision="%s"
%s
}}}""" % (revstring, reponame, rev, message)
    c = conn.cursor()
    c.execute("insert into ticket_change " + \
              "(ticket, time, author, field, newvalue) " + \
              "values (?, ?, ?, 'comment', ?)",
              (ticket, time_, author, comment))
    conn.commit()


def usage():
    print "add_changeset_comments.py /path/to/trac.db /path/to/repos"
    print
    print "  The hg repos in the 'repos' dir must exactly match the name"
    print "  of the repos in the trac db/ini."

if __name__ == "__main__":
    parser = OptionParser()
#    parser.add_option("--hint", action="append", default=[],
#        help="if string is found then line can't be end of INSERT")
    (options, args) = parser.parse_args()
    
    try:
        main(args[0], args[1])
    except (ValueError, IndexError):
        usage()
        sys.exit(1)
