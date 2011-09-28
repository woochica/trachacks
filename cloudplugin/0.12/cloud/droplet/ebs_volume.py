import os
from trac.web.chrome import add_notice, add_warning
from trac.util.translation import _

from cloud.droplet import Droplet

class EbsVolume(Droplet):
    """An EBS volume cloud droplet."""
    
    def render_grid(self, req):
        template,data,content_type = Droplet.render_grid(self, req)
        button = ('audit',_('Audit %(title)s',title=self.title))
        data['buttons'].append(button),
        return template, data, content_type
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        
        # prepare launch data
        launch_data = {}
        for field in ['size','zone','snapshot']:
            launch_data[field] = req.args.get(field,'')
        
        # prepare attributes
        attributes = {}
        fields = self.fields.get_list('crud_new', filter=r"cmd_.*")
        for field in fields:
            field.set_dict(attributes, req=req, default='')
        
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','ebs_create.py'))
        self._spawn(req, exe, launch_data, attributes)
    
    def save(self, req, id):
        req.perm.require('CLOUD_MODIFY')
        self.log.debug('Saving data bag item %s/%s..' % (self.name,id))
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # check to attach and/or detach volume to/from instance(s)
        new_instance_id = req.args.get('instance_id','')
        if 'instance_id' not in item or item['instance_id'] != new_instance_id:
            # check if attaching or detaching
            if 'instance_id' in item and item['instance_id']: # detach
                req.args['status'] = self.cloudapi.detach_ebs_volume(id,
                    item['instance_id'], item['device'])
            if new_instance_id: # attach
                req.args['status'] = self.cloudapi.attach_ebs_volume(id,
                    new_instance_id, req.args.get('device',''))
            else:
                req.args['device'] = ''
        
        # prepare fields; remove command fields
        fields = self.fields.get_list('crud_edit', filter=r"cmd_.*")
        for field in fields:
            field.set(item, req)
        item.save()
        self.log.info('Saved data bag item %s/%s' % (self.name,id))
        
        # show the view
        add_notice(req, _('%(label)s %(id)s has been saved.',
                          label=self.label, id=id))
        req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        self.log.debug('Deleting ebs volume and data bag item..')
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # delete the rds instance
        terminated = False
        id = 'undefined'
        try:
            id = item['id']
            self.cloudapi.delete_ebs_volume(id)
            terminated = True
            self.log.info('Deleted ebs volume %s' % id)
        except Exception, e:
            self.log.warn('Error deleting ebs volume %s:\n%s' % (id,str(e)))
        
        # delete item from chef
        item.delete()
        self.log.info('Deleted data bag item %s/%s' % (self.name,id))
        
        # show the grid
        if terminated:
            add_notice(req, _('%(label)s %(id)s has been deleted.',
                              label=self.label, id=id))
        else:
            add_warning(req,
                _("%(label)s %(id)s was not deleted as expected, " + \
                  "but its chef data bag item was deleted. " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=id))
        req.redirect(req.href.cloud(self.name))
        
    def audit(self, req, id):
        req.perm.require('CLOUD_MODIFY')
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','ebs_audit.py'))
        self._spawn(req, exe, {}, {})
