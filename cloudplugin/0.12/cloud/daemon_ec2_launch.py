#!/bin/python

import sys
import time
from daemon import Daemon

class Ec2Launcher(Daemon):
    """Launches and bootstraps an ec2 instance in a separate process."""
    
    STEPS = [
        'Launching the instance',
        'Starting up the instance',
        'Bootstrapping the instance',
        'Applying the chef roles and attributes',
    ]
    
    def __init__(self):
        Daemon.__init__(self, self.STEPS, "Launch Progress")
        
    def run(self, sysexit=True):
        # Step 1. Launching the instance
        self.log.debug('Launching instance..')
        self.progress.start(0)
        instance = self.cloudapi.launch_ec2_instance(
            image_id = self.launch_data['image_id'],
            instance_type = self.launch_data['instance_type'],
            zone = self.launch_data['zone'])
        self.progress.done(0)
        
        # update step 1 with id
        self.log.debug('Adding instance.id %s to progress' % instance.id)
        progress = self.progress.get()
        progress['steps'][0] += ' (%s)' % instance.id
        self.progress.set(progress)
        
        # Step 2. Starting up the instance
        self.log.debug('Starting up the instance..')
        self.progress.start(1)
        time.sleep(2.0) # instance can be a tad cranky when it launches
        self.cloudapi.wait_until_running(instance, timeout=600)
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
        node = self.chefapi.bootstrap(id, public_hostname, timeout=360)
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
        
        if sysexit:
            sys.exit(0) # success


if __name__ == "__main__":
    # launch
    daemon = Ec2Launcher()
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
