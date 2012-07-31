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
# This script is used to setup a new system with the software required for 
# a trac/svn/postgres/http server.
#

YUM=/usr/bin/yum
EASY_INSTALL=/usr/bin/easy_install
CHKCONFIG=/sbin/chkconfig

#Packages installed by Yum.
SYSTEM_PACKAGES="
subversion
python-devel
python-setuptools
python-sqlite
mod_dav_svn
mod_python
postgresql
postgresql-server
postgresql-python
postgresql-devel
gcc
httpd"

#Packages installed with easy_install.
#Use <package>==<version> to install a particular version of the package.
#Use <package> to install the latest version of the package.
PYTHON_PACKAGES="
Trac==0.11.1 
Genshi==0.5.1 
psycopg2==2.0.7"

SYSTEM_SERVICES="
httpd 
postgresql"

#Define to turn on a local python package repository.
#EASY_REPO="ftp://atmdev/pub/linux/"

if [ $EASY_REPO ]; then
	EASY_OPTS="-f $EASY_REPO"
else
	EASY_OPTS=""
fi

echo -e "\n** Installing system packages **"
$YUM install $SYSTEM_PACKAGES

echo -e "\n** Installing python packages **"
for package in $PYTHON_PACKAGES; do
	$EASY_INSTALL $EASY_OPTS $package
done

echo -e "\n** Enabling system runlevels **"
for service in $SYSTEM_SERVICES; do
	$CHKCONFIG $service on
done

