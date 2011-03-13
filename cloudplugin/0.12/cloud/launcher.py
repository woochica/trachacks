#!/bin/python

import sys
import time
import json
import tempfile
import logging
from optparse import OptionParser

from daemon import Daemon
from progress import Progress
from chefapi import ChefApi
from awsapi import AwsApi
from timer import Timer

class Launcher(Daemon):
    """Launches and bootstraps an ec2 instance in a separate process."""
    
    STEPS = [
        'Launching the instance',
        'Starting up the instance',
        'Bootstrapping the instance',
        'Applying the chef roles',
        'Starting supervised chef-client',
    ]
    
    def __init__(self, progress_file, chefapi, cloudapi,
                 launch_data, attributes, log):
        pidfile = tempfile.NamedTemporaryFile(delete=False).name
        Daemon.__init__(self, pidfile, log)
        self.progress = Progress(progress_file, self.pidfile, self.STEPS)
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        self.launch_data = launch_data
        self.attributes = attributes
        
    def run(self, sysexit=True):
        # Step 1. Launching the instance
        self.log.debug('Launching instance..')
        self.progress.start(0)
        instance = self.cloudapi.launch_instance(
            image_id = self.launch_data['image_id'],
            instance_type = self.launch_data['instance_type'],
            placement = self.launch_data['placement'])
        self.progress.done(0)
        
        # update step 1 with id
        self.log.debug('Adding instance.id %s to progress' % instance.id)
        progress = self.progress.get()
        progress['steps'][0] += ' (%s)' % instance.id
        self.progress.set(progress)
        
        # Step 2. Starting up the instance
        self.log.debug('Starting up the instance..')
        self.progress.start(1)
        self.cloudapi.wait_until_running(instance,timeout=600)
        if instance.state != 'running':
            msg = "Instance %s was launched" % instance.id + \
                  " but isn't running.  Check in the AWS" + \
                  " Management Console directly."
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        time.sleep(10.0) # instance is cranky when it wakes up
        self.progress.done(1)
        
        # add id to progress, update step 2 with public dns
        id = instance.private_dns_name
        self.log.debug('Adding id %s to progress' % id)
        progress = self.progress.get()
        progress['id'] = id
        progress['steps'][1] += ' (%s)' % instance.public_dns_name
        self.progress.set(progress)
        
        # Step 3. Bootstrapping the instance
        self.log.debug('Bootstrapping the instance..')
        self.progress.start(2)
        public_hostname = instance.public_dns_name
        node = self.chefapi.bootstrap(id, public_hostname, timeout=600)
        if node is None:
            msg = "Instance %s is running" % instance.id + \
                  " but not bootstrapped. Login to" + \
                  " %s to investigate." % instance.public_dns_name
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        self.progress.done(2)
        
        # Step 4. Applying the chef roles
        self.log.debug('Applying chef roles..')
        self.progress.start(3)
        self.log.debug('Saving node..')
        node = self.chefapi.resource('nodes', id)
        for field,value in self.attributes.items():
            if field == 'run_list':
                node.run_list = value # roles
            else:
                node.attributes.set_dotted(field, value)
        node.save()
        self.log.info('Saved node %s' % id)
        self.progress.done(3)
        
        # Step 5. Starting supervised chef-client
        self.log.debug('Running first chef-client..')
        self.progress.start(4)
        # get the first checkin time (from the bootstrap)
        timer = Timer(30)
        while timer.running:
            try:
                node = self.chefapi.resource('nodes', id)
                start = node['ohai_time']
                self.log.debug('Starting checkin time is %s' % start)
                break
            except KeyError:
                time.sleep(1.0)
        else:
            msg = "Timed out waiting to get ohai_time. Check" + \
                  " that the bootstrap succeeded properly."
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        # get the next checkin time (from the first supervised chef-client run)
        timer = Timer(600)
        while timer.running:
            time.sleep(5.0)
            node = self.chefapi.resource('nodes', id)
            if node['ohai_time'] != start:
                self.log.debug('End checkin time is %s' % node['ohai_time'])
                break
        else:
            msg = "Timed out waiting for first chef-client run." + \
                  " Check that the chef-client is properly supervised."
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        self.progress.done(4)
        
        if sysexit:
            sys.exit(0) # success


if __name__ == "__main__":
    # setup command line parsing
    parser = OptionParser()
    parser.add_option("-d", "--daemonize", default=False, action="store_true")
    parser.add_option("--progress-file")
    parser.add_option("--log-file")
    parser.add_option("--log-level", default=logging.DEBUG)
    parser.add_option("--chef-base-path")
    parser.add_option("--chef-boot-run-list", default=[], action='append')
    parser.add_option("--chef-boot-sudo", default=False, action="store_true")
    parser.add_option("--aws-key")
    parser.add_option("--aws-secret")
    parser.add_option("--aws-keypair")
    parser.add_option("--aws-keypair-pem")
    parser.add_option("--aws-username")
    parser.add_option("--placement")
    parser.add_option("--image-id")
    parser.add_option("--instance-type")
    parser.add_option("--attributes", default='{}', help="JSON dict")
    (options, _args) = parser.parse_args()
    
    # setup logging (presumes something else will rotate it)
    log = logging.getLogger("Launcher")
    log.setLevel(options.log_level)
    handler = logging.FileHandler(options.log_file)
    handler.setLevel(options.log_level)
    format = "%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s"
    handler.setFormatter(logging.Formatter(format))
    log.addHandler(handler)
    
    # setup apis
    chefapi = ChefApi(options.chef_base_path,
                      options.aws_keypair_pem,
                      options.aws_username,
                      options.chef_boot_run_list,
                      options.chef_boot_sudo,
                      log)
    
    cloudapi = AwsApi(options.aws_key,
                      options.aws_secret,
                      options.aws_keypair,
                      log)
    
    # prepare the data
    launch_data = {
        'placement': options.placement,
        'image_id':  options.image_id,
        'instance_type': options.instance_type,
    }
    
    attributes = json.loads(options.attributes)
    
    # launch
    launcher = Launcher(options.progress_file,
                        chefapi, cloudapi,
                        launch_data, attributes, log)
    try:
        if options.daemonize:
            launcher.start()
        else:
            launcher.run()
    except Exception, e:
            import traceback
            msg = "Launcher error: " + traceback.format_exc()+"\n"
            launcher.progress.error(msg)
            log.error(msg)
            handler.flush()
            sys.exit(1)
