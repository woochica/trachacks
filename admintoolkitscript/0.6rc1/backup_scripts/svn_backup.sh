#!/bin/bash
# Copyright (C) 2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Jeff Dever <deverj@navcanada.ca>
# 
###############################################################################
#
# This script is intended to be run from a cron job to perform backups
# for all the subversion repositories in SVN_ROOT.  No console output is
# produced unless there is a reported error.
#
# Ownership of files and directories will be as the privledges this script
# is run with.  If you want the owner to be apache you may wish to run this 
# with "sudo -u apache" or change the ownership and run as suid or just run as
# the apache user.  Up to you.
#
# There are three ways this script can be run:
#
# full 
# The repositories are locked when running.  A full snapshot of the repositories
# is taken and then compressed into an archive with the project name and 
# revision number as the file name. The repository datastore is preserved so
# these backups must be used with a same or similar version of svn programs.
# These directory trees are compressed and auto-rotated.  
# See hot_backup.py.
#
# incremental
# The repositories are not locked.  If there are no changes since the last 
# run, no backup is created.  This makes this a very cheap incremental backup
# that can be run frequently.  Files are not compressed or rotated as a
# complete set of the incrementals are required to restore from.  
# See svndump.py

# dump
# The repositories are not locked.  A full dump of the repositories is made 
# with a timestamp on the filename.  These full dumps are suitable for a load
# to a different major version of subversion and can be used with svndumpfilter 
# since the full contents are dumped (deltas not used).  Files are compressed
# but are not rotated.  
# See svnadmin help dump.


SVN_ROOT="/srv/svn"
SVN_BACKUP_ROOT="/srv.backup"
HOT_BACKUP="./hot-backup.py"
SVN_DUMP="./svndump.py"
SVNADMIN="/usr/bin/svnadmin"


#get the list of all valid repositories
repos=""
list="$SVN_ROOT/*"
for repo in $list; do
	if [ -d "$repo/db" ]; then
		repos="$repos $repo"
	fi
done

date=`date +%Y%m%d`

# process the command line arguments and run the command
command=$1
if [ $command == full ]; then

	backup_dir=$SVN_BACKUP_ROOT/full
	mkdir -p $backup_dir
	for repo in $repos; do
		$HOT_BACKUP --archive-type=bz2 $repo $backup_dir
	done

elif [ $command == incremental ]; then

	backup_dir=$SVN_BACKUP_ROOT/incremental
	mkdir -p $backup_dir
	for repo in $repos; do
		$SVN_DUMP $repo $backup_dir
	done

elif [ $command == dump ]; then

	backup_dir=$SVN_BACKUP_ROOT/dump
	mkdir -p $backup_dir

	for repo in $repos; do
		project=`basename $repo`
		archive=$backup_dir/$project.$date.svn
		$SVNADMIN dump --quiet $repo > $archive
		bzip2 $archive
	done

else
	cat <<EOF

svn_backup.sh [full|incremental|dump]
	full 		full backup of the repository tree
	incremental	incremental dump of latest changes
	dump		full dump suitable for migration

EOF

fi

