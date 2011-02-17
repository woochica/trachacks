import time
import boto

from timer import Timer

class AwsApi(object):
    """Wraps boto with several conveniences including:
    
     * launch an ec2 instance in one call
    """
    
    def __init__(self, key, secret, keypair, log):
        self.key = key.encode('ascii')
        self.secret = secret.encode('ascii')
        self.keypair = keypair
        self.log = log
        
    def launch_instance(self, image_id, instance_type, placement,
                        user_data=None, timeout=0):
        """Launch an ec2 instance.  If timeout is > 0, then this method
        won't return until the instance is fully running or the timeout
        duration expires."""
        # TODO: support multiple regions (and multiple security groups)
        conn = boto.connect_ec2(self.key, self.secret)
        image = conn.get_image(image_id)
        reservation = image.run(
            instance_type=instance_type,
            placement=placement,
            user_data=user_data,
            key_name=self.keypair)
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
            time.sleep(0.1)
            instance.update()
        return timer.running
    
    def terminate_instance(self, id):
        """Terminate an ec2 instance."""
        conn = boto.connect_ec2(self.key, self.secret)
        terminated = conn.terminate_instances([id])
        if terminated:
            terminated = terminated[0].id
        self.log.info('Terminated ec2 instance %s' % terminated)
        return terminated == id
