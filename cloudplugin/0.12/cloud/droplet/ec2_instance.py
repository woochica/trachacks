import os
from trac.web.chrome import add_notice, add_warning
from trac.util.translation import _

from cloud.droplet import Droplet

class Ec2Instance(Droplet):
    """An EC2 instance cloud droplet."""
    
    def render_grid(self, req):
        template,data,content_type = Droplet.render_grid(self, req)
        button = ('audit',_('Audit %(title)s',title=self.title))
        data['buttons'].append(button),
        return template, data, content_type
    
    def render_view(self, req, id):
        template,data,content_type = Droplet.render_view(self, req, id)
        if self._is_disable_api_termination(req, id):
            attrs = data.get('delete_attrs',{})
            attrs['disabled'] = 'disabled'
            data['delete_attrs'] = attrs
        return template, data, content_type
    
    def _is_disable_api_termination(self, req, id):
        # check chef data (not ec2 instance attribute data)
        node = self.chefapi.resource(self.crud_resource, id)
        field = self.fields['disable_api_termination']
        return field.get(node, req) in ('1','true')
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        
        # prepare launch data
        launch_data = {
            'zone': req.args.get('ec2.placement_availability_zone',''),
            'image_id': req.args.get('ec2.ami_id'),
            'instance_type': req.args.get('ec2.instance_type'),
            'volume': req.args.get('cmd_volume',''),
            'device': req.args.get('cmd_device',''),
            'disable_api_termination':
                req.args.get('disable_api_termination') in ('1','true'),
        }
        if launch_data['zone'] in ('No preference',''):
            launch_data['zone'] = None
        
        # prepare attributes
        attributes = {}
        fields = self.fields.get_list('crud_new', filter=r"(cmd_|ec2\.).*")
        for field in fields:
            field.set_dict(attributes, req=req, default='')
        
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','ec2_launch.py'))
        self._spawn(req, exe, launch_data, attributes)
    
    def save(self, req, id, fields=None, redirect=True):
        req.perm.require('CLOUD_MODIFY')
        self.log.debug('Saving node..')
        node = self.chefapi.resource(self.crud_resource, id)
        
        # update instance attributes
        instance_id = node.attributes.get_dotted('ec2.instance_id')
        self.cloudapi.modify_ec2_instance(instance_id,
            req.args.get('disable_api_termination') in ('1','true'))
        
        # prepare fields; remove automatic (ec2) fields
        if fields is None:
            fields = self.fields.get_list('crud_edit', filter=r"(cmd_|ec2\.).*")
        for field in fields:
            field.set(node, req)
        node.save()
        self.log.info('Saved node %s' % id)
        
        if redirect:
            # show the view
            add_notice(req, _('%(label)s %(id)s has been saved.',
                              label=self.label, id=id))
            req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        self.log.debug('Deleting instance, node, and client..')
        node = self.chefapi.resource(self.crud_resource, id)
        
        # delete the ec2 instance
        instance_id = 'undefined'
        try:
            instance_id = node.attributes.get_dotted('ec2.instance_id')
            terminated = self.cloudapi.terminate_ec2_instance(instance_id)
            if terminated:
                self.log.info('Terminated instance %s (%s)' % \
                              (instance_id,terminated))
        except Exception, e:
            self.log.warn('Error terminating instance %s:\n%s' % \
                          (instance_id,str(e)))
            terminated = False
        
        if terminated is None:
            # disable_api_termination is enabled
            add_warning(req,
                _("%(label)s %(id)s (id=%(instance_id)s) was not " + \
                  "terminated; it's protected from termination. " + \
                  "Run an audit to update the chef data.",
                  label=self.label, id=id, instance_id=instance_id))
            req.redirect(req.href.cloud(self.name,id))
        
        # delete node from chef
        node.delete()
        self.log.info('Deleted node %s' % id)
        
        # delete the client from chef (so we can reuse the key)
        client = self.chefapi.resource('clients', id)
        client.delete()
        self.log.info('Deleted client %s' % id)
        
        # show the grid
        if terminated:
            add_notice(req, _('%(label)s %(id)s has been deleted.',
                              label=self.label, id=instance_id))
        else:
            add_warning(req,
                _("%(label)s %(id)s (id=%(instance_id)s) was not " + \
                  "terminated as expected, but its chef node was deleted. " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=id, instance_id=instance_id))
        req.redirect(req.href.cloud(self.name))
        
    def audit(self, req, id):
        req.perm.require('CLOUD_MODIFY')
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','ec2_audit.py'))
        self._spawn(req, exe, {}, {})
