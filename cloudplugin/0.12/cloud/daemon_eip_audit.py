#!/bin/python

import sys
from daemon import Daemon

class EipAuditor(Daemon):
    """Audits the eip addresses in a separate process."""
    
    def __init__(self):
        Daemon.__init__(self, ['Determining differences..'], "Audit Progress",
            "Auditing actual EIP addresses for discrepancies with chef")
        
    def run(self, sysexit=True):
        # first determine the steps
        bag = self.chefapi.resource('data', name=self.databag)
        addresses = self.cloudapi.get_eip_addresses()
        
        self.log.debug('Determining id deltas..')
        chef_ids = [id for id in bag]
        cloud_ids = [a.public_ip.replace('.','_') for a in addresses]
        adds = [id for id in cloud_ids if id not in chef_ids]
        updates = [id for id in cloud_ids if id in chef_ids]
        deletes = [id for id in chef_ids if id not in cloud_ids]
        
        self.log.debug('Generating steps..')
        steps = []
        for id in adds:
            steps.append("Add eip instance '%s' to chef" % id)
        for id in updates:
            steps.append("Update eip instance '%s' in chef" % id)
        for id in deletes:
            steps.append("Delete eip instance '%s' from chef" % id)
        self.progress.steps(steps)
        step = 0
        
        # Add and Updates Steps
        for ids in [adds,updates]:
            for address in addresses:
                self.progress.start(step)
                id = address.public_ip.replace('.','_')
                if id not in ids: continue
                
                # update and save the audited fields
                item = self.chefapi.databagitem(bag, id)
                if item is None:
                    msg = "Data bag item %s/%s " % (bag.name,id) + \
                      "timed out when attempted to be retrieved."
                    self.log.debug(msg)
                    self.progress.error(msg)
                    sys.exit(1)
                
                item['public_ip'] = address.public_ip
                item['instance_id'] = address.instance_id
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
    daemon = EipAuditor()
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
