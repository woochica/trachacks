#!/bin/bash
# Copyright (C) 2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Jeff Dever <deverj@navcanada.ca>
#
# SYNCHRONIZE-MIRRORS
#
# This script is intended to run as a post-commit svn hook to synchronize
# remote repository mirrors after every commit.  When calling this script
# from the hook the following arguments must be supplied:
#
#   [1] REPOS-PATH   (the path to this repository)
#
# Neither the default working directory or the environment are assumed.
#
# The repository mirrors file should list the URL of each repository mirror
# but not include the repository name itself: just the top level repos 
# directory as the repository is determined from the provided REPOS-PATH.
# These mirrors must be already pre-configured for the svnsync to perform
# the synchronization.
#
# Errors are logged to the syslog facility to /var/log/messages.

MIRRORS_FILE=/srv/svn/mirrors
SVNSYNC=/usr/bin/svnsync
USERNAME=svnsync
PASSWORD=svnsync
SYNC_OPTIONS="--non-interactive --no-auth-cache "

repos_path=$1
project=`basename $repos_path`

# Writes an error message to the syslog
function log_error {
	logger -s -p local1.error -t svnmirror $1
}

if ! [ -e $MIRRORS_FILE ]; then
	log_error "Unable to find mirrors file '$MIRRORS_FILE'"
	exit 1 #failed
fi

for mirror_url in $( cat $MIRRORS_FILE ); do
	$SVNSYNC synchronize $SYNC_OPTIONS --username $USERNAME --password $PASSWORD $mirror_url/$project
	if [ $? != 0 ]; then
		log_error "Failed to update mirror '$mirror_url' for project '$project'"
	fi
done
exit 0 #success

