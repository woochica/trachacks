#!/bin/python

import sys
import time

from cloud.daemon import Daemon

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
        self.volume_id = self.launch_data['volume']
        self.device = self.launch_data['device']
        if self.volume_id:
            steps = self.STEPS[:2]+['Attaching the ebs volume']+self.STEPS[2:]
            progress = self.progress.get()
            progress['steps'] = steps
            self.progress.set(progress)
        
    def run(self, sysexit=True):
        # Step 1. Launching the instance
        step = 0
        self.log.debug('Launching instance..')
        self.progress.start(step)
        instance = self.cloudapi.launch_ec2_instance(
            image_id = self.launch_data['image_id'],
            instance_type = self.launch_data['instance_type'],
            zone = self.launch_data['zone'],
            disable_api_termination =
                self.launch_data['disable_api_termination'])
        self.progress.done(step)
        
        # update step 1 with id
        self.log.debug('Adding instance.id %s to progress' % instance.id)
        progress = self.progress.get()
        progress['steps'][step] += ' (%s)' % instance.id
        self.progress.set(progress)
        
        # Step 2. Starting up the instance
        step += 1
        self.log.debug('Starting up the instance..')
        self.progress.start(step)
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
        self.progress.done(step)
        
        # add id to progress, update step 2 with public dns
        id = instance.private_dns_name
        self.log.debug('Adding id %s to progress' % id)
        progress = self.progress.get()
        progress['id'] = id
        progress['steps'][step] += ' (%s)' % instance.public_dns_name
        self.progress.set(progress)
        
        # Step 3 (optional). Attaching the ebs volume
        if self.volume_id:
            step += 1
            self.log.debug('Attaching the ebs volume..')
            self.progress.start(step)
            status = self.cloudapi.attach_ebs_volume(
                id = self.volume_id,
                instance_id = instance.id,
                device = self.device)
            if status != "in-use":
                msg = "Error attaching volume %s" % self.volume_id + \
                      " to instance %s.  Status is '%s'" % (instance.id,status)
                self.log.error(msg)
                self.progress.error(msg)
                sys.exit(1)
            progress = self.progress.get()
            progress['steps'][step] += ' (%s)' % self.volume_id
            self.progress.set(progress)
            
            # save the volume and device info to its data bag
            self.log.debug('Saving ebs data bag %s..' % self.volume_id)
            bag = self.chefapi.resource('data', name='ebs')
            item = self.chefapi.databagitem(bag, self.volume_id)
            item['instance_id'] = instance.id
            item['device'] = self.device
            item['status'] = status
            item.save()
            self.log.info('Saved ebs data bag %s' % self.volume_id)
            self.progress.done(step)
        
        # Step 4. Bootstrapping the instance
        step += 1
        self.log.debug('Bootstrapping the instance..')
        self.progress.start(step)
        public_hostname = instance.public_dns_name
        run_list = self.attributes.get('run_list')
        node = self.chefapi.bootstrap(id, public_hostname, run_list)
        if node is None:
            msg = "Instance %s is running" % instance.id + \
                  " but not bootstrapped. Login to" + \
                  " %s to investigate." % instance.public_dns_name
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        self.progress.done(step)
        
        # Step 5. Applying the chef roles
        step += 1
        self.log.debug('Applying chef roles..')
        self.progress.start(step)
        self.log.debug('Saving node..')
        node = self.chefapi.resource('nodes', id)
        for field,value in self.attributes.items():
            if field == 'run_list':
                node.run_list = value # roles
            else:
                node.attributes.set_dotted(field, value)
        node.save()
        self.log.info('Saved node %s' % id)
        self.progress.done(step)
        
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
