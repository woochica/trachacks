import time
import boto

from timer import Timer

class AwsApi(object):
    """Wraps boto with several conveniences including:
    
     * launch an ec2 instance in one call
    """
    
    def __init__(self, key, secret, keypair, username, password, log):
        self.key = key.encode('ascii')
        self.secret = secret.encode('ascii')
        self.keypair = keypair
        self.username = username
        self.password = password
        self.log = log
    
    
    # EC2 Instances
    
    def launch_ec2_instance(self, image_id, instance_type, zone, user_data=None,
                            disable_api_termination=False, timeout=0):
        """Launch an ec2 instance.  If timeout is > 0, then this method
        won't return until the instance is fully running or the timeout
        duration expires."""
        # TODO: support multiple regions (and multiple security groups)
        conn = boto.connect_ec2(self.key, self.secret)
        image = conn.get_image(image_id)
        reservation = image.run(
            instance_type=instance_type,
            placement=zone,
            user_data=user_data,
            key_name=self.keypair,
            disable_api_termination=disable_api_termination)
        instance = reservation.instances[0]
        self.log.info('Launched ec2 instance %s' % instance.id)
        
        if timeout:
            time.sleep(5.0) # avoids intermittent error
            self.wait_until_running(instance,timeout)
        
        return instance
    
    def wait_until_running(self, instance, timeout=120):
        """Returns after the instance is running.  Returns True if the
        instance is running before the 'timeout' duration (seconds)."""
        timer = Timer(timeout)
        while instance.state == 'pending' and timer.running:
            time.sleep(1.0)
            instance.update()
        return timer.running
    
    def modify_ec2_instance(self, id, disable_api_termination):
        """Modify an ec2 instance."""
        instance = self.get_ec2_instances(id)[0]
        result = instance.modify_attribute('disableApiTermination',
                                            disable_api_termination)
        return result
    
    def terminate_ec2_instance(self, id):
        """Terminate an ec2 instance.  Returns True if terminated
        successfully, False if terminated unsuccessfuly, and None
        if the disable_api_termination attribute is enabled."""
        conn = boto.connect_ec2(self.key, self.secret)
        
        # first check if termination is protected
        import pydevd; pydevd.settrace('10.0.2.15')
        instance = self.get_ec2_instances(id)[0]
        attr = instance.get_attribute('disableApiTermination')
        if attr['disableApiTermination'] == 'true':
            return None
        
        # not protected so terminate
        terminated = conn.terminate_instances([id])
        if terminated:
            terminated = terminated[0].id
        self.log.info('Terminated ec2 instance %s' % terminated)
        return terminated == id
    
    def get_ec2_instances(self, id=None):
        """Retrieve ec2 instance(s)."""
        self.log.info('Geting ec2 instances (id=%s)..' % id)
        conn = boto.connect_ec2(self.key, self.secret)
        if isinstance(id,str) or isinstance(id,unicode):
            id = [id]
        reservations = conn.get_all_instances(id)
        return [reservation.instances[0] for reservation in reservations]
    
    
    # RDS Instances
    
    def launch_rds_instance(self, id, dbname, allocated_storage, instance_class,
                            availability_zone, multi_az=False, timeout=0):
        """Launch an rds instance.  If timeout is > 0, then this method
        won't return until the rds instance is fully running or the timeout
        duration expires."""
        # TODO: support multiple regions (and multiple security groups)
#        import logging
#        boto.set_file_logger('rds', '/tmp/boto.log', level=logging.DEBUG)
#        conn = boto.connect_rds(self.key, self.secret, debug=2)
        conn = boto.connect_rds(self.key, self.secret)
        instance = conn.create_dbinstance(id, allocated_storage, instance_class,
                        self.username, self.password, db_name=dbname,
                        availability_zone=availability_zone, multi_az=multi_az)
        self.log.info('Launched rds instance %s' % instance.id)
        
        if timeout:
            time.sleep(5.0) # avoids intermittent error
            self.wait_until_endpoint(instance, timeout)
        
        return instance
    
    def wait_until_endpoint(self, instance, timeout=120):
        """Returns after the rds instance's endpoint is available.  Returns
        True if the instance is running before the 'timeout' duration
        (seconds)."""
        timer = Timer(timeout)
        while instance.endpoint == None and timer.running:
            time.sleep(1.0)
            instance.update()
        return timer.running

    def modify_rds_instance(self, id, allocated_storage=None,
                            instance_class=None, multi_az=None,
                            apply_immediately=False):
        """Modify an rds instance."""
        conn = boto.connect_rds(self.key, self.secret)
        conn.modify_dbinstance(id,
            allocated_storage = allocated_storage,
            instance_class = instance_class,
            multi_az = multi_az,
            apply_immediately = apply_immediately)
        self.log.info('Modified rds instance %s' % id)
    
    def delete_rds_instance(self, id):
        """Terminate an rds instance."""
        self.log.info('Deleting rds instance %s..' % id)
        conn = boto.connect_rds(self.key, self.secret)
        conn.delete_dbinstance(id, skip_final_snapshot=True)
        self.log.info('Deleted rds instance %s' % id)
    
    def get_rds_instances(self, id=None):
        """Retrieve rds instance(s)."""
        self.log.info('Geting rds instances (id=%s)..' % id)
        conn = boto.connect_rds(self.key, self.secret)
        return conn.get_all_dbinstances(id)
    
    
    # EIP Addresses
    
    def allocate_eip_address(self):
        """Allocate a new eip address."""
        conn = boto.connect_ec2(self.key, self.secret)
        address = conn.allocate_address()
        self.log.info('Created eip address %s' % address)
        return address

    def modify_eip_association(self, ip, instance_id=None):
        """Associate an eip address with an ec2 instance if provided,
        else it disassociates the eip address from any ec2 instance."""
        conn = boto.connect_ec2(self.key, self.secret)
        if instance_id:
            result = conn.associate_address(instance_id, ip)
            self.log.info('Associated ec2 instance %s with eip address %s' % \
                            (instance_id, ip))
        else:
            result = conn.disassociate_address(ip)
            self.log.info('Disassociated eip address %s' % ip)
        return result
    
    def release_eip_address(self, ip):
        """Release eip address."""
        self.log.info('Release eip address %s..' % ip)
        conn = boto.connect_ec2(self.key, self.secret)
        result = conn.release_address(ip)
        self.log.info('Released eip address %s' % ip)
        return result
    
    def get_eip_addresses(self, ip=None):
        """Retrieve rds instance(s)."""
        if ip is None:
            ip = []
        elif isinstance(ip,str):
            ip = [ip]
        self.log.info('Geting eip addresses (ip=%s)..' % ip)
        conn = boto.connect_ec2(self.key, self.secret)
        return conn.get_all_addresses(ip)
