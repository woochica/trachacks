#!/bin/python

import sys
import tempfile
import logging
from optparse import OptionParser

from daemon import Daemon
from progress import Progress
from chefapi import ChefApi
from awsapi import AwsApi

class Ec2Auditor(Daemon):
    """Audits the ec2 instances in a separate process."""
    
    def __init__(self, progress_file, chefapi, cloudapi, log):
        pidfile = tempfile.NamedTemporaryFile(delete=False).name
        Daemon.__init__(self, pidfile, log)
        self.progress = Progress(progress_file, self.pidfile,
                                 steps=['Determining differences..'],
                                 title="Audit Progress")
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        
    def run(self, sysexit=True):
        # first determine the steps
        nodes = self.chefapi.resource('nodes')
        instances = self.cloudapi.get_ec2_instances()
        
        self.log.debug('Determining id deltas..')
        chef_names = [name for name in nodes]
        cloud_names = [instance.private_dns_name for instance in instances]
        adds = [id for id in cloud_names if id not in chef_names]
        deletes = [id for id in chef_names if id not in cloud_names]
        
        self.log.debug('Generating steps..')
        steps = []
        for id in adds:
            steps.append("Missing ec2 instance '%s' in chef" % id)
        for id in deletes:
            steps.append("Extra ec2 instance '%s' in chef" % id)
        self.progress.steps(steps)
        
        # Indicate differences (as errors)
        for step in range(len(steps)):
            self.progress.start(step)
        
        # Reveal discrepancies
        if steps:
            msg = "The above discrepancies must be resolved manually. " + \
                  " The AWS Management Console may be of some help."
            self.progress.error(msg)
            sys.exit(1)
        
        # No discrepancies
        self.progress.steps(['No discrepancies'])
        self.progress.start(0)
        self.progress.done(0)
        
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
    (options, _args) = parser.parse_args()
    
    # setup logging (presumes something else will rotate it)
    log = logging.getLogger("Ec2Auditor")
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
    
    # launch
    daemon = Ec2Auditor(options.progress_file, chefapi, cloudapi, log)
    try:
        if options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "Ec2Auditor error: " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            log.error(msg)
            handler.flush()
            sys.exit(1)
