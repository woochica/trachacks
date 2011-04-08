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

class RdsLauncher(Daemon):
    """Launches and bootstraps an rds instance in a separate process."""
    
    STEPS = [
        'Launching the rds instance',
        'Starting up the rds instance',
        'Saving the chef roles and attributes',
    ]
    
    def __init__(self, progress_file, databag, chefapi, cloudapi,
                 launch_data, attributes, log):
        pidfile = tempfile.NamedTemporaryFile(delete=False).name
        Daemon.__init__(self, pidfile, log)
        self.progress = Progress(progress_file, self.pidfile, self.STEPS,
                                 title="Launch Progress")
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        self.databag = databag
        self.launch_data = launch_data
        self.attributes = attributes
        
    def run(self, sysexit=True):
        # Step 1. Launching the rds instance
        self.log.debug('Launching rds instance..')
        self.progress.start(0)
        id = self.launch_data['id']
        instance = self.cloudapi.launch_rds_instance(
            id = id,
            storage = self.launch_data['storage'],
            class_ = self.launch_data['class'],
            dbname = self.launch_data['dbname'],
            zone = self.launch_data['zone'],
            multi_az = self.launch_data['multi_az'])
        self.progress.done(0)
        
        # update step 1 with id
        self.log.debug('Adding id %s to progress' % id)
        progress = self.progress.get()
        progress['id'] = id
        progress['steps'][0] += ' (%s)' % id
        self.progress.set(progress)
        
        # Step 2. Starting up the rds instance
        self.log.debug('Starting up the rds instance..')
        self.progress.start(1)
        time.sleep(2.0) # instance can be a tad cranky when it launches
        self.cloudapi.wait_until_endpoint(instance, timeout=1800)
        if instance.endpoint == None:
            msg = "RDS Instance %s was launched" % id + \
                  " but doesn't have an endpoint (yet).  Check" + \
                  " in the AWS Management Console directly."
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        self.progress.done(1)
        
        # add id to progress, update step 2 with public dns
        endpoint = "%s:%s" % instance.endpoint
        self.log.debug('Adding endpoint %s to progress' % endpoint)
        progress = self.progress.get()
        progress['steps'][1] += ' (%s)' % endpoint
        self.progress.set(progress)
        
        # Step 4. Applying the chef roles and attributes
        self.log.debug('Applying chef roles and attributes..')
        self.progress.start(2)
        self.log.debug('Saving data bag item %s/%s..' % (self.databag,id))
        rds = self.chefapi.resource('data', name=self.databag)
        item = self.chefapi.databagitem(rds, id)
        for field,value in self.attributes.items():
            item[field] = value
        item.save()
        self.log.info('Saved data bag item %s/%s..' % (self.databag,id))
        self.progress.done(2)
        
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
    parser.add_option("--rds-username")
    parser.add_option("--rds-password")
    parser.add_option("--databag")
    parser.add_option("--launch-data", default='{}', help="JSON dict")
    parser.add_option("--attributes", default='{}', help="JSON dict")
    (options, _args) = parser.parse_args()
    
    # setup logging (presumes something else will rotate it)
    log = logging.getLogger("RdsLauncher")
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
                      options.rds_username,
                      options.rds_password,
                      log)
    
    # prepare the data
    launch_data = json.loads(options.launch_data)
    attributes = json.loads(options.attributes)
    
    # launch
    daemon = RdsLauncher(options.progress_file, options.databag,
                         chefapi, cloudapi, launch_data, attributes, log)
    try:
        if options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "RdsLauncher error: " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            log.error(msg)
            handler.flush()
            sys.exit(1)
