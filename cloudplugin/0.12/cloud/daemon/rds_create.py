#!/bin/python

import sys
import time

from cloud.daemon import Daemon

class RdsCreator(Daemon):
    """Creates an rds instance in a separate process."""
    
    STEPS = [
        'Creating the rds instance',
        'Starting up the rds instance',
        'Saving the chef roles and attributes',
    ]
    
    def __init__(self):
        Daemon.__init__(self, self.STEPS, "Create Progress")
        
    def run(self, sysexit=True):
        # Step 1. Launching the rds instance
        self.log.debug('Creating rds instance..')
        self.progress.start(0)
        id = self.launch_data['id']
        instance = self.cloudapi.launch_rds_instance(
            id = id,
            dbname = self.launch_data['dbname'],
            allocated_storage = self.launch_data['allocated_storage'],
            instance_class = self.launch_data['instance_class'],
            availability_zone = self.launch_data['availability_zone'],
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
        
        # update step 2 with endpoint
        endpoint = "%s:%s" % instance.endpoint
        self.log.debug('Adding endpoint %s to progress' % endpoint)
        progress = self.progress.get()
        progress['steps'][1] += ' (%s)' % endpoint
        self.progress.set(progress)
        
        # Step 3. Applying the chef roles and attributes
        self.log.debug('Applying chef roles and attributes..')
        self.progress.start(2)
        self.log.debug('Saving data bag item %s/%s..' % (self.databag,id))
        bag = self.chefapi.resource('data', name=self.databag)
        item = self.chefapi.databagitem(bag, id)
        
        # copy all instance's string attributes
        for field,value in instance.__dict__.items():
            if isinstance(value,unicode) or isinstance(value,str):
                item[field.lower()] = value
        item['endpoint'] = instance.endpoint[0]
        item['endpoint_port'] = instance.endpoint[1]
        
        # set the passed in attributes
        for field,value in self.attributes.items():
            item[field] = value
            
        item.save()
        self.log.info('Saved data bag item %s/%s..' % (self.databag,id))
        self.progress.done(2)
        
        if sysexit:
            sys.exit(0) # success


if __name__ == "__main__":
    daemon = RdsCreator()
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
