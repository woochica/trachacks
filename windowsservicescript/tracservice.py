#!C:\programme\python\2.3\python.exe
# -*- coding: iso8859-1 -*-
#
# Author: Florent Xicluna <laxyf@yahoo.fr>


# The service module defines a single class (TracWindowsService) that contains
# the functionality for running Trac as a Windows Service.
# 
# To use this class, users must do the following:
# 1. Download and install the win32all package
#    (http://starship.python.net/crew/mhammond/win32/)
# 2. Edit the constants section with the proper information.
# 3. Open a command prompt and navigate to the directory where this file
#    is located.  Use one of the following commands to
#    install/start/stop/remove the service:
#    > tracservice.py install
#    > tracservice.py start
#    > tracservice.py stop
#    > tracservice.py remove
#    Additionally, typing "tracservice.py" will present the user with all of the
#    available options.
#
# Once installed, the service will be accessible through the Services
# management console just like any other Windows Service.  All service 
# startup exceptions encountered by the TracWindowsService class will be 
# viewable in the Windows event viewer (this is useful for debugging
# service startup errors); all application specific output or exceptions that
# are not captured by the standard Trac logging mechanism should 
# appear in the stdout/stderr logs.
#

import locale
import sys
import os

import win32serviceutil
import win32service

from trac.web.standalone import BasicAuth, DigestAuth, TracHTTPServer

# ==  Editable CONSTANTS SECTION  ============================================

PYTHON = r'C:\Python23\python.exe'
INSTANCE_HOME = r'c:\path\to\instance\trac'

# Trac options (see C:\Python23\Script\tracd)
OPTS = [
  ( '--auth', ('trac,%s\conf\htdigest,TracRealm' % INSTANCE_HOME) ),
  ( '--port', '80' ),
]

# ==  End of CONSTANTS SECTION  ==============================================

# Other constants
PYTHONDIR = os.path.split(PYTHON)[0]
PYTHONSERVICE_EXE=r'%s\Lib\site-packages\win32\pythonservice.exe' % PYTHONDIR
LOG_DIR = r'%s\log' % INSTANCE_HOME

# Trac instance(s)
ARGS = [ INSTANCE_HOME, ]

def add_auth(auths, vals, cls):
    info = vals.split(',', 3)
    p, h, r = info
    if auths.has_key(p):
        print >>sys.stderr, 'Ignoring duplicate authentication option for ' \
                            'project: %s' % p
    else:
        auths[p] = cls(h, r)

class TracWindowsService(win32serviceutil.ServiceFramework):
    """Trac Windows Service helper class.

    The TracWindowsService class contains all the functionality required
    for running Trac application as a Windows Service.

    For information on installing the application, please refer to the
    documentation at the end of this module or navigate to the directory
    where this module is located and type "tracservice.py" from the command
    prompt.
    """

    _svc_name_ = 'Trac_%s' % str(hash(INSTANCE_HOME))
    _svc_display_name_ = 'Trac instance at %s' % INSTANCE_HOME
    _exe_name_ = PYTHONSERVICE_EXE

    def SvcDoRun(self):
        """ Called when the Windows Service runs. """

        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.httpd = self.trac_init()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        try:
            self.httpd.serve_forever()
        except OSError:
            sys.exit(1)

    def SvcStop(self):
        """Called when Windows receives a service stop request."""

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.httpd:
            self.httpd.server_close()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def trac_init(self):
        """ Checks for the required data and initializes the application. """

        locale.setlocale(locale.LC_ALL, '')
        port = 80
        hostname = ''
        auths = {}
        daemonize = 0
        env_parent_dir = None

        for o, a in OPTS:
            if o in ("-a", "--auth"):
                add_auth(auths, a, DigestAuth)
            if o == '--basic-auth':
                add_auth(auths, a, BasicAuth)
            if o in ("-p", "--port"):
                port = int(a)
            elif o in ("-b", "--hostname"):
                hostname = a
            if o in ("-e", "--env-parent-dir"):
                env_parent_dir = a

        if not env_parent_dir and not ARGS:
            raise ValueError("""No Trac project specified""")

        sys.stdout = open(os.path.join(LOG_DIR, 'stdout.log'),'a')
        sys.stderr = open(os.path.join(LOG_DIR, 'stderr.log'),'a')

        server_address = (hostname, port)
        return TracHTTPServer(server_address, env_parent_dir, ARGS, auths)

if __name__ == '__main__':
    # The following are the most common command-line arguments that are used
    # with this module:
    #  tracservice.py install (Installs the service with manual startup)
    #  tracservice.py --startup auto install (Installs the service with auto startup)    
    #  tracservice.py start (Starts the service)
    #  tracservice.py stop (Stops the service)
    #  tracservice.py remove (Removes the service)
    #
    # For a full list of arguments, simply type "tracservice.py".
    win32serviceutil.HandleCommandLine(TracWindowsService)
