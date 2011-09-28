# Original version:
# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

import sys, os, time, atexit
from signal import SIGTERM 
import json
import tempfile
import logging
from optparse import OptionParser

from cloud.progress import Progress
from cloud.api.chef2 import Chef
from cloud.api.aws import Aws

try:
    import xmpp #@UnresolvedImport
except:
    pass

class Daemon(object):
    """
    A generic daemon class with added support for chef/cloud apis and
    communicating with other processes via a progress file.
    
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, steps, title, description='', can_continue=False):
        # setup command line parsing
        parser = OptionParser()
        parser.add_option("-d","--daemonize",default=False,action="store_true")
        parser.add_option("--trac-base-url")
        parser.add_option("--progress-file")
        parser.add_option("--log-file")
        parser.add_option("--log-level", default=logging.DEBUG)
        parser.add_option("--chef-base-path")
        parser.add_option("--chef-boot-run-list", default=[], action='append')
        parser.add_option("--chef-boot-sudo",default=False, action="store_true")
        parser.add_option("--chef-boot-version")
        parser.add_option("--aws-key")
        parser.add_option("--aws-secret")
        parser.add_option("--aws-keypair")
        parser.add_option("--aws-keypair-pem")
        parser.add_option("--aws-username")
        parser.add_option("--aws-security-groups")
        parser.add_option("--rds-username")
        parser.add_option("--rds-password")
        parser.add_option("--databag")
        parser.add_option("--launch-data", default='{}', help="JSON dict")
        parser.add_option("--attributes", default='{}', help="JSON dict")
        parser.add_option("--started-by")
        parser.add_option("--notify-jabber")
        parser.add_option("--jabber-server")
        parser.add_option("--jabber-port")
        parser.add_option("--jabber-username")
        parser.add_option("--jabber-password")
        parser.add_option("--jabber-channel")
        (self.options, _args) = parser.parse_args()
        
        # setup logging (presumes something else will rotate it)
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(self.options.log_level)
        self.handler = logging.FileHandler(self.options.log_file)
        self.handler.setLevel(self.options.log_level)
        format = "%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s"
        self.handler.setFormatter(logging.Formatter(format))
        self.log.addHandler(self.handler)
        
        # setup apis
        self.chefapi = Chef(self.options.chef_base_path,
                               self.options.aws_keypair_pem,
                               self.options.aws_username,
                               self.options.chef_boot_run_list,
                               self.options.chef_boot_sudo,
                               self.options.chef_boot_version,
                               self.log)
        
        self.cloudapi = Aws(self.options.aws_key,
                               self.options.aws_secret,
                               self.options.aws_keypair,
                               self.options.aws_security_groups,
                               self.options.rds_username,
                               self.options.rds_password,
                               self.log)
        
        # prepare the data
        self.databag = self.options.databag
        self.launch_data = json.loads(self.options.launch_data)
        self.attributes = json.loads(self.options.attributes)
        
        # prepare progress
        command = ''
        if can_continue:
            command = ['/usr/bin/python'] + sys.argv
        self.pidfile = tempfile.NamedTemporaryFile(delete=False).name
        self.progress = Progress(self.options.progress_file,
                                 self.pidfile, steps, title, description,
                                 {'0':(time.time(),None)},
                                 started_by=self.options.started_by,
                                 command=command)
        self.progress.pidfile(self.pidfile) # in case this is a restart
        
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e: 
            self.log.critical("fork 1 failed: %d (%s)\n" %(e.errno, e.strerror))
            sys.exit(1)
    
        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 
    
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            self.log.critical("fork 2 failed: %d (%s)\n" %(e.errno, e.strerror))
            sys.exit(1) 
        
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
    
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, ValueError):
            pid = None
    
        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            self.log.critical(message % self.pidfile)
            sys.exit(1)
        
        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
    
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            self.log.critical(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be
        called after the process has been daemonized by start() or restart().
        """
        
    def notify_jabber(self, message, resource='command', ignore_errors=True):
        """Sends a message to a jabber channel."""
        if not self.options.notify_jabber:
            return
        
        # append progress url to message
        if not self.options.trac_base_url.endswith('/'):
            self.options.trac_base_url += '/'
        url = self.options.trac_base_url + \
                'cloud/%s?action=progress&file=%s' % \
                (resource,self.options.progress_file)
        message += ': %s' % url
        
        try:
            # send message
            jid = xmpp.protocol.JID(self.options.jabber_username)
            cl = xmpp.Client(jid.getDomain(), debug=[])
            
            server = (self.options.jabber_server,int(self.options.jabber_port))
            if not cl.connect(server=server, use_srv=False):
                raise Exception("Could not connect to jabber server %s:%s" % \
                                    server)
                
            if not cl.auth(jid.getNode(), self.options.jabber_password):
                raise Exception("Could not authenticate jabber user '%s'" % \
                                    self.options.jabber_username)
            
            user = self.options.jabber_username.split('@')[0]
            cl.send(xmpp.Presence('%s/%s' % (self.options.jabber_channel,user)))
            #cl.sendInitPresence(requestRoster=0)
            msg = xmpp.Message(self.options.jabber_channel, message)
            msg.setType('groupchat')
            cl.send(msg)
            time.sleep(1)
            cl.disconnect()
        except:
            if not ignore_errors:
                raise
            # don't let a jabber issue block deployment or other commands
