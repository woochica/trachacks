import os
import time
import signal
import urllib2
from subprocess import Popen, STDOUT, PIPE

import chef
from chef.exceptions import ChefServerNotFoundError
from timer import Timer

class ChefApi(object):
    """Wraps pychef with several conveniences including:
    
      * search params and result conversion
      * data bag item ordering
      * generalized resource querying
      * generalized resource creation
      * ec2 instance bootstrapping
    """
    
    def __init__(self, base_path, keypair_pem, user, boot_run_list, sudo, log):
        self.base_path = os.path.abspath(base_path)
        self.keypair_pem = keypair_pem
        self.user = user
        self.boot_run_list = boot_run_list
        self.sudo = sudo
        self.log = log
        self.chef = chef.autoconfigure(self.base_path)
    
    def search(self, index, sort=None, asc=1, limit=1000, offset=0, q='*:*'):
        """Search the chefserver and return a list of dict items.  Since
        sorting only partially worked in chef 0.9 and doesn't work at all
        in chef 0.10, we do sorting here on the client."""
        
        def get_value(item):
            if sort == 'name':
                return item.name
            if sort == 'run_list':
                return item.run_list
            try:
                if hasattr(item.attributes, 'get_dotted'):
                    return item.attributes.get_dotted(sort)
                return item[sort]
            except KeyError:
                return ''
        
        # convert rows to resource objects (e.g., nodes)
        timer = Timer(60.0)
        while True:
            try:
                rows = []
                search = chef.search.Search(index, q, rows=10000, api=self.chef)
                self.log.debug("About to query chef at %s" % search.url)
                for result in search:
                    rows.append(result.object)
                if sort:
                    rows.sort(key=get_value, reverse=not asc)
                return rows[offset:offset+limit], search.total
            except TypeError, e:
                # workaround for race condition when row was just deleted
                if not timer.running:
                    raise
                self.log.debug("Encountered error %s, retrying.." % str(e))
                time.sleep(1.0)
            except ChefServerNotFoundError:
                return [], 0
    
    def resource(self, resource, id=None, name=None):
        """Query chef for a resource and return the result as a dict (or
        dict-like) record.  A dict-like record is returned for 'nodes'
        and 'roles' resources which lazy-loads its value."""
        self.log.debug("Querying chef api resource '%s'" % resource)
        if resource == 'nodes':
            if id:
                return chef.node.Node(id, self.chef)
            return chef.node.Node.list(self.chef)
        if resource == 'roles':
            if id:
                return chef.role.Role(id, self.chef)
            return chef.role.Role.list(self.chef)
        if resource == 'data':
            if id and name:
                return chef.data_bag.DataBagItem(name, id, self.chef)
            if name:
                bag = chef.data_bag.DataBag(name, self.chef)
                if not bag.exists:
                    bag.save()
                return bag
            return chef.data_bag.DataBag.list(self.chef)
        if resource == 'clients':
            if id:
                return chef.client.Client(id, self.chef)
            return chef.client.Client.list(self.chef)
        raise Exception("Unknown resource '%s'" % resource)
    
    def create(self, resource, id=None, name=None):
        """Creates the given chef resource."""
        if resource == 'nodes':
            return chef.node.Node.create(id, self.chef)
        if resource == 'roles':
            return chef.role.Role.create(id, self.chef)
        if resource == 'data':
            if id and name:
                return chef.data_bag.DataBagItem.create(name, id, self.chef)
            if name:
                bag = chef.data_bag.DataBag.create(name, self.chef)
                if not bag.exists:
                    bag.save()
        if resource == 'clients':
            return chef.client.Client.create(id, self.chef)
        raise Exception("Unknown resource '%s'" % resource)
    
    def databag(self, bag_name, id=None):
        """If id is provided, then the specific data bag is returned.
        Else a list of all data items (dicts) in the given data bag
        will be returned.  If a data item has an 'order' field,
        it will be used to order the returned list."""
        bag = chef.data_bag.DataBag(bag_name, self.chef)
        ids = id and [id] or bag
        
        items = []
        for id in ids:
            item = self.databagitem(bag, id)
            items.append( (int(item.get('order',99)),item) )
        return [item for (u_order,item) in sorted(items)]
    
    def databagitem(self, bag, id, create=False, timeout=45.0):
        """Returns the named data bag item from the provided data bag."""
        timer = Timer(timeout)
        while timer.running:
            try:
                if create:
                    self.log.debug("Creating %s/%s data bag item" % (bag.name,id))
                    return chef.data_bag.DataBagItem.create(bag.name, id, self.chef)
                else:
                    self.log.debug("Getting data bag item %s/%s.." % (bag.name,id))
                    return bag[id]
            except KeyError:
                create = True
                return self.databagitem(bag, id, create, timeout)
            except urllib2.URLError, e:
                self.log.debug(".. got %s, retrying.." % str(e))
                time.sleep(1.0)
        self.log.debug("Timeout on data bag item %s/%s" % (bag.name,id))
        return None
    
    def bootstrap(self, id, hostname, timeout=300):
        """Bootstraps an ec2 instance by calling out to "knife bootstrap".
        The result should be that the ec2 instance connects with the
        chefserver.
        
        This routine handles the race condition when the bootstrap tries
        to connect to the chefserver after the instance's chef-client
        starts but before it creates the client.pem file causing the
        bootstrap to fail with a 409 permission error.  In this case, the
        routine will simply attempt to bootstrap again until it succeeds
        or until the given timeout period expires.
        """
        class Alarm(Exception): pass
        def alarm_handler(signum, frame): raise Alarm
        
        cmd = '/usr/bin/knife bootstrap %s' % hostname
        cmd += ' -c %s' % os.path.join(self.base_path,'knife.rb')
        cmd += ' -x %s' % self.user
        if self.keypair_pem:
            cmd += ' -i %s' % self.keypair_pem
        if self.boot_run_list:
            cmd += ' -r %s' % ','.join(r for r in self.boot_run_list)
        if self.sudo:
            cmd += ' --sudo'
            
        expected_transient_errors = [
            "409 Conflict: Client already exists",
            "409 Conflict: Node already exists",
            "Connection refused - connect(2)",
            "No route to host - connect(2)",
            "Connection timed out - connect(2)",
            "Failed to authenticate",
        ]
        
        attempt = 1
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)
        timer = Timer(timeout)
        while timer.running:
            self.log.debug('Bootstrapping %s with command: %s' % (id,cmd))
            p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
            out = ''
            
            try:
                out = unicode(p.communicate()[0], 'utf-8', 'ignore')
                signal.alarm(0) # clear the alarm
            except Alarm:
                p.kill()
            
            for error in expected_transient_errors:
                if error in out:
                    self.log.info('Retrying due to transient error %s' % error)
                    break
            else: # no transient error found ..
                # .. but check for chef error or possible ssh error
                if attempt == 1 and \
                   (not out or 'ERROR: Exception handlers complete' in out):
                    if not out:
                        self.log.info('possible ssh problem - trying again..')
                        signal.signal(signal.SIGALRM, alarm_handler)
                        signal.alarm(timeout)
                        timer = Timer(timeout)
                    else:
                        self.log.info('Chef error - trying again..')
                    attempt += 1
                    continue # try just one more time
                break # .. so break out of while loop
        else:
            # timer ran out after the last (possibly only) bootstrap attempt
            self.log.info('Timed out bootstrapping %s with:\n%s' % (id,out))
            return None
        
        if p.returncode != 0 or 'ERROR: Exception handlers complete' in out:
            self.log.info('Error bootstrapping %s:\n%s' % (id,out))
            return None
        
        self.log.info('Bootstrapped %s (id=%s):\n%s' % (hostname,id,out))
        return chef.node.Node(id, self.chef)
