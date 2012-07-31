# Copyright (C) 2008-2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Mike Stoddart <stoddam@navcanada.ca>

import os

#Installed location of the admin scripts.
INSTALL_DIR = os.environ["HOME"] + "/admintoolkit"

#The root for all Trac environments and Subversion repositories
#managed by the scripts.
ROOT_PATH = "/srv"

#Root of the SVN repository tree.
SVN_ROOT = ROOT_PATH + os.sep + "svn"

#Root of the Trac environment tree.
TRAC_ROOT = ROOT_PATH + os.sep + "trac"

#Configuration directory
CONF_ROOT = ROOT_PATH + os.sep + "conf"

#Download directory
DOWNLOAD_ROOT = ROOT_PATH + os.sep + "download"

#Database service name.
DB_SERVICE = "postgresql"

#System default database directory.
DB_DEFAULT = "/var/lib/pgsql"

#Database directory
DB_ROOT = ROOT_PATH + os.sep + "pgsql"

#Database host name.
DB_HOST = "localhost"

#Database trac administrator username.
DB_USER = "postgres"

#Database trac admin password.
#Leave blank to be prompted when using admin tools.
DB_PASSWD = ""

#Web server service name.
HTTPD_SERVICE = "httpd"

#Root of the apache webserver configuration.
HTTPD_CONF_ROOT = "/etc/httpd/conf.d"

#Subversion mirrors file.
SVN_MIRRORS_FILE = CONF_ROOT + os.sep + "mirrors"

#SVN default directory template for initial repository creation.
REPO_TEMPLATE = INSTALL_DIR + os.sep + "svn_skel"

#Temporary file used by the scripts.
TEMP_FILE = "/tmp/trac-admin-TEMP"

#Used by scripts when adding Trac permissions. Controls the display of output.
VERIFY_USER_PERMISSIONS = False

#Full paths to system executables.
SERVICE = "/sbin/service"
SVNLOOK = "/usr/bin/svnlook"
SVNSYNC = "/usr/bin/svnsync"
SVNADMIN = "/usr/bin/svnadmin"
SVN = "/usr/bin/svn"
SUDO = "/usr/bin/sudo"
TRACADMIN = "/usr/bin/trac-admin"
HTPASSWD = "/usr/bin/htpasswd"
CREATEUSER = "/usr/bin/createuser"
CHKCONFIG = "/sbin/chkconfig"

#The username svnsync is performed on behalf of
SVNSYNC_USERNAME = "svnsync"

#The password for the SVNSYNC_USERNAME.
SVNSYNC_PASSWORD = "svnsync"

#Regular expression for allowed project names
PROJECT_RE = "^[A-Za-z][A-Za-z0-9_-]*$"

#Regular expression for user names
USER_RE = "^[a-z]+$"

#Regular expression for group names
GROUP_RE = "^[a-z_-]+$"

