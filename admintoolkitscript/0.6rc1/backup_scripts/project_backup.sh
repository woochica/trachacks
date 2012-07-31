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
# for files for a given project .  There is no console output unless
# an error occurs.
#
# Ownership of files and directories will be as the privledges this script
# is run with.  If you want the owner to be apache you may wish to run this 
# with "sudo -u apache" or change the ownership and run as suid or just run as
# the apache user.  Up to you.
#
# There is only one way this script can be run:
#
# project
# A full directory copy of all the project files and project database.


SRV_ROOT="/srv"
BACKUP_ROOT="/tmp/backup"
SERVICE="/sbin/service"
TAR="/bin/tar"
PGDUMP="/usr/bin/pg_dump"
DBUSER="postgres"

function print_usage {
	cat <<EOF

project_backup.sh [project] <project_name>
	full		backup of all files for a project

EOF
}


# process the command line arguments and run the command
if [ $# == 2 ]; then
	command=$1
	project=$2
else
	print_usage
	exit -1
fi

date=`date +%Y%m%d`

if [ $command == full ]; then

	backup_dir=$BACKUP_ROOT/project
	mkdir -p $backup_dir
	archive=$backup_dir/$project.$date.tar
	log=$backup_dir/$project.$date.log

	echo "*** Starting backup for $project ***" > $log
	#stop the webserver and database
	$SERVICE httpd stop >>$log

	#echo "backup the project directory structure"
	cd $SRV_ROOT
	echo "Creating archive $archive" >>$log
	$TAR cf $archive */$project* >>$log

	#echo "dump the project database"
	archive=$backup_dir/$project.$date.sql
	echo "Exporting database $archive" >>$log
	$PGDUMP $project -U $DBUSER > $archive

	#start the webserver and database 
	$SERVICE httpd start >>$log

else
	print_usage
	exit -2
fi

exit 0

