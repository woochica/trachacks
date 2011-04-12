#!/bin/python

import sys
import tempfile
import logging
from optparse import OptionParser

from daemon import Daemon
from progress import Progress
from chefapi import ChefApi
from awsapi import AwsApi

class RdsAuditor(Daemon):
    """Audits the rds instances in a separate process."""
    
    def __init__(self, progress_file, databag, chefapi, cloudapi, log):
        pidfile = tempfile.NamedTemporaryFile(delete=False).name
        Daemon.__init__(self, pidfile, log)
        self.progress = Progress(progress_file, self.pidfile,
                                 steps=['Determining differences..'],
                                 title="Audit Progress")
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        self.databag = databag
        
    def run(self, sysexit=True):
        # first determine the steps
        bag = self.chefapi.resource('data', name=self.databag)
        instances = self.cloudapi.get_rds_instances()
        
        self.log.debug('Determining id deltas..')
        chef_ids = [id for id in bag]
        cloud_ids = [instance.id for instance in instances]
        adds = [id for id in cloud_ids if id not in chef_ids]
        updates = [id for id in cloud_ids if id in chef_ids]
        deletes = [id for id in chef_ids if id not in cloud_ids]
        
        self.log.debug('Generating steps..')
        steps = []
        for id in adds:
            steps.append("Add rds instance '%s' to chef" % id)
        for id in updates:
            steps.append("Update rds instance '%s' in chef" % id)
        for id in deletes:
            steps.append("Delete rds instance '%s' from chef" % id)
        self.progress.steps(steps)
        step = 0
        
        # Add and Updates Steps
        for ids in [adds,updates]:
            for instance in instances:
                self.progress.start(step)
                id = instance.id
                if id not in ids: continue
                
                # update and save the audited fields
                item = self.chefapi.databagitem(bag, id)
                if item is None:
                    msg = "Data bag item %s/%s " % (bag.name,id) + \
                      "timed out when attempted to be retrieved."
                    self.log.debug(msg)
                    self.progress.error(msg)
                    sys.exit(1)
                
                # copy all instance's string attributes
                for field,value in instance.__dict__.items():
                    if type(value) in (unicode,str,int,float,bool):
                        item[field.lower()] = value
                item['endpoint'] = instance.endpoint[0]
                item['endpoint_port'] = instance.endpoint[1]
                
                self.log.debug('Saving data bag item %s/%s..' % (bag.name,id))
                item.save()
                self.log.debug('Saved data bag item %s/%s' % (bag.name,id))
                self.progress.done(step)
                step += 1
        
        # Deletes Steps
        for id in deletes:
            self.progress.start(step)
            item = self.chefapi.databagitem(bag, id)
            item.delete()
            self.progress.done(step)
            step += 1
        
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
    (options, _args) = parser.parse_args()
    
    # setup logging (presumes something else will rotate it)
    log = logging.getLogger("RdsAuditor")
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
    daemon = RdsAuditor(options.progress_file, options.databag,
                        chefapi, cloudapi, log)
    try:
        if options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "RdsAuditor error: " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            log.error(msg)
            handler.flush()
            sys.exit(1)
