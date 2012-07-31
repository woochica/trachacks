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
# for all the trac environments in TRAC_ROOT.  There is no console output unless
# an error occurs.
#
# Ownership of files and directories will be as the privledges this script
# is run with.  If you want the owner to be apache you may wish to run this 
# with "sudo -u apache" or change the ownership and run as suid or just run as
# the apache user.  Up to you.
#
# There is only one way this script can be run:
#
# full 
# The server is stopped for the duration of the backup.  A full snapshot of 
# the trac environments is taken along with the database.  Compression is used
# but no rotation is done.
#
# dump
# A dump of each database that corresponds to a trac environment is dumped
# to a seperate file.  Useful for migrating single projects to another server.
# Compression is used but no rotation is done.
# 
# dump_all
# A full dump of all the databases in the sql server instance is dumped to a 
# single file.  Useful for a migration to a new pgsql version or architecture.
# Compression is used but no rotation is done.


TRAC_ROOT="/srv/trac"
TRAC_BACKUP_ROOT="/srv.backup"
DB_ROOT="/var/lib/pgsql/data"
APACHECTL="/usr/sbin/apachectl"
PGCTL="/usr/bin/pg_ctl"
PGDUMP="/usr/bin/pg_dump"
PGDUMPALL="/usr/bin/pg_dumpall"
SERVICE="/sbin/service"
TAR="/bin/tar"
BZIP2="/usr/bin/bzip2"

#get the list of all valid environments
envs=""
list="$TRAC_ROOT/*"
for env in $list; do
	if [ -d "$env/conf" ]; then
		envs="$envs $env"
	fi
done

date=`date +%Y%m%d`

# process the command line arguments and run the command
command=$1
if [ $command == full ]; then

	backup_dir=$TRAC_BACKUP_ROOT/full
	mkdir -p $backup_dir

	#stop the webserver and database
	$SERVICE httpd stop >/dev/null
	$SERVICE postgresql stop >/dev/null 

	#do the actual backup
	trac_archive=$backup_dir/trac-$date.tar.bz2
	db_archive=$backup_dir/pgsql-$date.tar.bz2
	cd `dirname $TRAC_ROOT`
	$TAR cjf $trac_archive `basename $TRAC_ROOT`
	cd `dirname $DB_ROOT`
	$TAR cjf $db_archive `basename $DB_ROOT`

	#start the webserver and database 
	$SERVICE httpd start >/dev/null
	$SERVICE postgresql start >/dev/null 

elif [ $command == dump ]; then

	#make the backup directory as needed
	backup_dir=$TRAC_BACKUP_ROOT/dump
	mkdir -p $backup_dir
	
	#add an environment for postgres
	envs="postgres $envs"

	for db in $envs; do
		project=`basename $db`

		#dump the project database
		archive=$backup_dir/$project.$date.sql
		$PGDUMP $project -U postgres > $archive
		if [ -s $archive ]; then
			$BZIP2 $archive
		fi

	done

elif [ $command == dump_dirs ]; then

	#make the backup directory as needed
	backup_dir=$TRAC_BACKUP_ROOT/dump
	mkdir -p $backup_dir
	
	#do commands from the trac root directory
	cd $TRAC_ROOT

	for db in $envs; do
		project=`basename $db`

		#tar up the trac environment directory
		archive=$backup_dir/$project.$date.tar
		$TAR cf $archive $project 
		$BZIP2 $archive

	done


elif [ $command == dump_all ]; then

	backup_dir=$TRAC_BACKUP_ROOT/dump_all
	mkdir -p $backup_dir

	archive=$backup_dir/all.sql.$date
	$PGDUMPALL -U postgres > $archive
	if [ -s $archive ]; then
		$BZIP2 $archive
	else
		echo Failed to write backup file $archive
	fi

else
	cat <<EOF

trac_backup.sh [full|dump|dump_dirs|dump_all]
	full 		full backup of the database and trac directory
	dump		individual dump of each project database
	dump_dirs	individual dump of each project directory 
	dump_all	full dump of all databases

EOF

fi

