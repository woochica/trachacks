#!/bin/python

import sys

from cloud.daemon import Daemon

class Ec2Auditor(Daemon):
    """Audits the ec2 instances in a separate process."""
    
    def __init__(self):
        Daemon.__init__(self, ['Determining differences..'], "Audit Progress",
            "Auditing actual EC2 instances for discrepancies with chef")
        
    def run(self, sysexit=True):
        # first determine the steps
        nodes = self.chefapi.resource('nodes')
        instances = self.cloudapi.get_ec2_instances()
        
        self.log.debug('Determining id deltas..')
        chef_names = [name for name in nodes]
        cloud_names = [instance.private_dns_name for instance in instances]
        adds = [id for id in cloud_names if id and id not in chef_names]
        updates = [id for id in cloud_names if id and id in chef_names]
        deletes = [id for id in chef_names if id and id not in cloud_names]
        
        self.log.debug('Generating steps..')
        steps = []
        for id in updates:
            steps.append("Updating ec2 instance '%s' in chef" % id)
        for id in adds:
            steps.append("Missing ec2 instance '%s' in chef" % id)
        for id in deletes:
            steps.append("Extra ec2 instance '%s' in chef" % id)
        self.progress.steps(steps)
        
        # update chef
        for step in range(len(updates)):
            self.progress.start(step)
            id = updates[step]
            node = nodes[id]
            instance_id = node.attributes.get_dotted('ec2.instance_id')
            instance = self.cloudapi.get_ec2_instances(instance_id)[0]
            attr = instance.get_attribute('disableApiTermination')
            node['disable_api_termination'] = attr['disableApiTermination']
            node.save()
            self.progress.done(step)
        
        # indicate differences (as errors)
        for step in range(len(updates), len(steps)):
            self.progress.start(step)
        
        # reveal discrepancies
        if adds or deletes:
            msg = "The above discrepancies must be resolved manually. " + \
                  " The AWS Management Console may be of some help."
            self.progress.error(msg)
            sys.exit(1)
        
        # No discrepancies
        if not steps:
            self.progress.steps(['No discrepancies'])
            self.progress.start(0)
            self.progress.done(0)
        
        if sysexit:
            sys.exit(0) # success


if __name__ == "__main__":
    daemon = Ec2Auditor()
    try:
        if daemon.options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "Oops.. " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            daemon.log.error(msg)
            daemon.handler.flush()
            sys.exit(1)
