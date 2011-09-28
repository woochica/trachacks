#!/bin/python

import sys
import time

from cloud.daemon import Daemon

class EbsCreator(Daemon):
    """Creates an ebs volume in a separate process."""
    
    STEPS = [
        'Creating the ebs volume',
        'Starting up the ebs volume',
        'Applying the chef roles and attributes',
    ]
    
    def __init__(self):
        Daemon.__init__(self, self.STEPS, "Create Progress")
        
    def run(self, sysexit=True):
        # Step 1. Launching the ebs volume
        step = 0
        self.log.debug('Creating ebs volume..')
        self.progress.start(step)
        volume = self.cloudapi.create_ebs_volume(
            size = self.launch_data['size'],
            zone = self.launch_data['zone'],
            snapshot = self.launch_data['snapshot'])
        self.progress.done(step)
        
        # update step 1 with id
        id = volume.id
        self.log.debug('Adding id %s to progress' % id)
        progress = self.progress.get()
        progress['id'] = id
        progress['steps'][step] += ' (%s)' % id
        self.progress.set(progress)
        
        # Step 2. Starting up the ebs volume
        step += 1
        self.log.debug('Starting up the ebs volume..')
        self.progress.start(step)
        time.sleep(1.0)
        self.cloudapi.wait_until_available(volume, timeout=120)
        if volume.status != 'available':
            msg = "EBS Volume %s was launched" % id + \
                  " but isn't available (yet).  Check" + \
                  " in the AWS Management Console directly."
            self.log.error(msg)
            self.progress.error(msg)
            sys.exit(1)
        self.progress.done(step)
        
        # Step 3. Applying the chef roles and attributes
        step += 1
        self.log.debug('Applying chef roles and attributes..')
        self.progress.start(step)
        self.log.debug('Saving data bag item %s/%s..' % (self.databag,id))
        bag = self.chefapi.resource('data', name=self.databag)
        item = self.chefapi.databagitem(bag, id)
        
        # copy all volume's string attributes
        for field,value in volume.__dict__.items():
            if isinstance(value,unicode) or isinstance(value,str):
                item[field.lower()] = value
        
        # set the passed in attributes
        for field,value in self.attributes.items():
            item[field] = value
            
        item.save()
        self.log.info('Saved data bag item %s/%s..' % (self.databag,id))
        self.progress.done(step)
            
        if sysexit:
            sys.exit(0) # success


if __name__ == "__main__":
    daemon = EbsCreator()
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
