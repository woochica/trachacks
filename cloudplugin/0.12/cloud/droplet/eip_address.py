import os
from trac.web.chrome import add_notice, add_warning
from trac.util.translation import _

from cloud.droplet import Droplet

class EipAddress(Droplet):
    """An EIP address cloud droplet."""
    
    def render_grid(self, req):
        template,data,content_type = Droplet.render_grid(self, req)
        button = ('audit',_('Audit %(title)s',title=self.title))
        data['buttons'].append(button),
        return template, data, content_type
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        self.log.debug('Allocating new eip..')
        
        # allocate eip address
        address = self.cloudapi.allocate_eip_address()
        public_ip = address.public_ip
        instance_id = req.args.get('instance_id')
        self.cloudapi.modify_eip_association(public_ip, instance_id)
        
        # create or update the data bag item
        id = public_ip.replace('.','_')
        self.chefapi.resource('data', name=self.name) # creates data bag
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        fields = self.fields.get_list('crud_new', filter=r"cmd_.*")
        for field in fields:
            field.set(item, req)
        item['public_ip'] = public_ip
        item.save()
        self.log.info('Saved data bag item %s/%s' % (self.name,id))
        
        add_notice(req, _('%(label)s %(public_ip)s has been created.',
                          label=self.label, public_ip=public_ip))
        req.redirect(req.href.cloud(self.name, id))
    
    def save(self, req, id, fields=None, redirect=True):
        req.perm.require('CLOUD_MODIFY')
        self.log.debug('Saving data bag item %s/%s..' % (self.name,id))
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # modify eip address
        public_ip = item['public_ip']
        instance_id = req.args.get('instance_id')
        self.cloudapi.modify_eip_association(public_ip, instance_id)
        
        # save to chef - prepare fields; remove command fields
        if fields is None:
            fields = self.fields.get_list('crud_edit', filter=r"cmd_.*")
        for field in fields:
            field.set(item, req)
        item.save()
        self.log.info('Saved data bag item %s/%s' % (self.name,id))
        
        if redirect:
            # show the view
            add_notice(req, _('%(label)s %(id)s has been saved.',
                              label=self.label, id=id))
            req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        self.log.debug('Releasing eip address and data bag item..')
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # release the eip address
        released = self.cloudapi.release_eip_address(item['public_ip'])
        
        # delete item from chef
        item.delete()
        self.log.info('Deleted data bag item %s/%s' % (self.name,id))
        
        # show the grid
        if released:
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
                os.path.dirname(__file__),'..','daemon','eip_audit.py'))
        self._spawn(req, exe, {}, {})
