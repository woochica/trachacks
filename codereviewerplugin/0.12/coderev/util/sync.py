#! /usr/bin/python
# -*- coding: UTF-8 -*-
# 
# Sample sync utility for sqlite3 dbs and git repos that updates the
# codereviewer_map table.

import os
import re
import sys
import sqlite3
from subprocess import Popen, STDOUT, PIPE

EPOCH_MULTIPLIER = 1000000.0


def sync(db_path, repo_dir):
    db = sqlite3.connect(db_path)
    reponame = os.path.basename(repo_dir.rstrip('/')).lower()
    
    # extract changesets to sync
    changeset_lines = get_changeset_lines(repo_dir)
    print "processing %d changesets" % len(changeset_lines)
    
    # purge table for this repo
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM codereviewer_map
        WHERE repo='%s'
    """ % reponame)
    
    # insert a row per ticket in commit message
    for changeset_line in changeset_lines:
        print '.',
        rev,when,msg = changeset_line.split('|',2)
        when = long(when) * EPOCH_MULTIPLIER
        ticket_re = re.compile('#([0-9]+)')
        for ticket in ticket_re.findall(msg):
            try:
                cursor.execute("""
                    INSERT INTO codereviewer_map
                        (repo,changeset,ticket,time)
                    VALUES ('%s','%s','%s',%s);
                    """ % (reponame,rev,ticket,when))
            except sqlite3.IntegrityError:
                print "\nduplicate %s, %s, #%s" % (reponame,rev,ticket)
    db.commit()

def get_changeset_lines(repo_dir):
    """Return all changesets including their commit time and message
    pipe-delimited in chronological order."""
    cmds = ['cd %s' % repo_dir, 'git log --reverse --format="%H|%ct|%s"']
    return execute(' && '.join(cmds)).splitlines()

def execute(cmd):
    p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
    out = p.communicate()[0]
    if p.returncode != 0:
        raise Exception('cmd: %s\n%s' % (cmd,out))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        file = os.path.basename(sys.argv[0])
        print "usage: %s <db_path> <repo_dir>" % file
        sys.exit(1)
    
    # sync
    db_path = sys.argv[1]
    repo_dir = sys.argv[2]
    sync(db_path,repo_dir)
