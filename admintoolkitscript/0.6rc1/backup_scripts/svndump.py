#!/usr/bin/python

# backup a given svn repository incrementaly 
# the resulting dumpfile will be in the form
# repos_name.dump.0-19
#

import os
import sys
from string import rfind, replace

debug = 0
svn_backup_dir = '/var/log/svn_backup'

def get_youngest_rev(path):
    """
    """
    youngest_cmd = "/usr/bin/svnlook youngest " + path
    cmdout = os.popen(youngest_cmd)
    rev= cmdout.read()
    rev= int(rev.strip())
    cmdout.close()
    return rev

def get_youngest_rev_dumpfile(backup_dir, repos_name):
    """
    get the revision number from the latest dumpfile
    """
    rev_ranges = []
    for f in os.listdir(backup_dir):
        if f.startswith(repos_name) and (f != repos_name):
            this_rev_range = map(int, f[rfind(f, '.')+1:].split('-'))
            rev_ranges.extend(this_rev_range)
    if (len(rev_ranges) == 0):
        return 0
    rev_ranges.sort()
    if (debug):
        print "...revision ranges on disk: ", rev_ranges
    return rev_ranges[-1]

def dump(backup_dir, repos_path, lower_rev, upper_rev):
    if (debug == 1):
        print "...doing an incremental backup"
        run_quiet = ''
    else:
        run_quiet = ' --quiet'

    if (upper_rev - lower_rev) == 1:
        range = str(upper_rev)
    else:
        range = str(lower_rev+1) + ":" + str(upper_rev)

    dumpfile_path = backup_dir + '/' + \
                    os.path.split(repos_path)[-1] + \
                    ".dump." + replace(range, ':', '-')

    dump_cmd = "/usr/bin/svnadmin dump --incremental " + \
           repos_path + run_quiet + " -r " +  range + " > " + dumpfile_path

    if (debug == 1):
        print "...RANGE: ", range
        print "...dumpfile fullpath: ", dumpfile_path
        print "...cmd: ", dump_cmd

    cmdout = os.popen(dump_cmd)
    cmdout.close()

def usage():
    print "usage: %s REPOS_PATH BACKUP_DIR\n" %(sys.argv[0])
    #print "\n"
    #print ""
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        usage()

    repos_path = sys.argv[1]
    backup_dir = sys.argv[2]
    if not os.path.exists(repos_path):
        print "REPOS_PATH: %s does not exist" %(repos_path)
        system.exit(1)
    if not os.path.exists(backup_dir):
        print "BACKUP_DIR: %s does not exist" %(backup_dir)
        system.exit(1)

    if (debug):
        print "...repository path: ", repos_path
        print "...backup dir: ", backup_dir

    if repos_path[-1] == '/':
        repos_path = repos_path[:-1]

    repos_name = os.path.split(repos_path)[-1]
    youngest_rev_svn = get_youngest_rev(repos_path)
    youngest_rev_dumpfile = get_youngest_rev_dumpfile(backup_dir, repos_name)

    if (debug):
        print "...youngest rev in dumpfile: ", youngest_rev_dumpfile
        print "...youngest rev in svn: ", youngest_rev_svn


    if youngest_rev_dumpfile == youngest_rev_svn:
        if (debug):
            print "...the backup is up to date."
    elif youngest_rev_dumpfile > youngest_rev_svn:
        if (debug):
            print "...last revision backed up is larger than in svn."
    else:
        dump(backup_dir, repos_path, youngest_rev_dumpfile, youngest_rev_svn)

    if (debug):
        print "...done."

if __name__ == '__main__':
    main()

