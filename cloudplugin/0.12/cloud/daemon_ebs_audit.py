#!/bin/python

import sys
from daemon import Daemon

class EbsAuditor(Daemon):
    """Audits the ebs volumes in a separate process."""
    
    def __init__(self):
        Daemon.__init__(self, ['Determining differences..'], "Audit Progress",
            "Auditing actual EBS volumes for discrepancies with chef")
        
    def run(self, sysexit=True):
        # first determine the steps
        bag = self.chefapi.resource('data', name=self.databag)
        instances = self.cloudapi.get_ebs_volumes()
        
        self.log.debug('Determining id deltas..')
        chef_ids = [id for id in bag]
        cloud_ids = [instance.id for instance in instances]
        adds = [id for id in cloud_ids if id not in chef_ids]
        updates = [id for id in cloud_ids if id in chef_ids]
        deletes = [id for id in chef_ids if id not in cloud_ids]
        
        self.log.debug('Generating steps..')
        steps = []
        for id in adds:
            steps.append("Add ebs volume '%s' to chef" % id)
        for id in updates:
            steps.append("Update ebs volume '%s' in chef" % id)
        for id in deletes:
            steps.append("Delete ebs volume '%s' from chef" % id)
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
                
                # extract attachment data
                item['instance_id'] = instance.attach_data.instance_id or ''
                item['device'] = instance.attach_data.device or ''
                    
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
    daemon = EbsAuditor()
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
