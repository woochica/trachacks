# Copyright (C) 2008-2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Mike Stoddart <stoddam@navcanada.ca>

import os

"""
The root for all Trac environments and Subversion repositories
managed by the scripts.
"""
ROOT_PATH = os.sep + "srv"

"""
The password file that will be used by Apache to restrict
access to Trac environments and Subversion repositories.
"""
PASSWORD_FILE = ROOT_PATH + os.sep + ".htpasswd"

"""
Temporary file used by the scripts.
"""
TEMP_FILE = "/tmp/trac-admin-TEMP"

"""
Hostname for the Postgresqt server.
"""
HOSTNAME = "localhost"

"""
Used by scripts when adding Trac permissions. Controls the
display of output.
"""
VERIFY_USER_PERMISSIONS = False

"""
Used to define the location of the "service" binary.
"""
SERVICE_BINARY = "/sbin/service"

"""
Defines the password for the admin user in the password file (.htpasswd)
"""
ADMIN_PASSWORD="admin"
