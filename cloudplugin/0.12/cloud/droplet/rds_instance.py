import copy
import os
from trac.web.chrome import add_notice, add_warning
from trac.util.translation import _

from cloud.droplet import Droplet

class RdsInstance(Droplet):
    """An RDS instance cloud droplet."""
    
    def render_grid(self, req):
        template,data,content_type = Droplet.render_grid(self, req)
        button = ('audit',_('Audit %(title)s',title=self.title))
        data['buttons'].append(button),
        return template, data, content_type
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        
        # prepare launch data
        launch_data = {}
        for field in ['id','dbname','allocated_storage','instance_class',
                      'availability_zone','multi_az']:
            launch_data[field] = req.args.get(field,'')
        if launch_data['availability_zone'] in ('No preference',''):
            launch_data['availability_zone'] = None
        launch_data['multi_az'] = launch_data['multi_az'] in ('1','true')
        
        # prepare attributes
        attributes = copy.copy(launch_data)
        filter = '('+'|'.join(launch_data.keys())+')'
        fields = self.fields.get_list('crud_new', filter=filter)
        for field in fields:
            field.set_dict(attributes, req=req, default='')
        
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','rds_create.py'))
        self._spawn(req, exe, launch_data, attributes)
    
    def save(self, req, id, fields=None, redirect=True):
        req.perm.require('CLOUD_MODIFY')
        self.log.debug('Saving data bag item %s/%s..' % (self.name,id))
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # prepare modify data
        self.cloudapi.modify_rds_instance(id,
            allocated_storage = req.args.get('allocated_storage'),
            instance_class = req.args.get('instance_class'),
            multi_az = req.args.get('multi_az'),
            apply_immediately = req.args.get('cmd_apply_now'))

        # prepare fields; remove command fields
        if fields is None:
            fields = self.fields.get_list('crud_edit', filter=r"cmd_.*")
        for field in fields:
            field.set(item, req)
        item['multi_az'] = item['multi_az'] in ('1','true')
        item.save()
        self.log.info('Saved data bag item %s/%s' % (self.name,id))
        
        if redirect:
            # show the view
            add_notice(req, _('%(label)s %(id)s has been saved.',
                              label=self.label, id=id))
            req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        self.log.debug('Deleting rds instance and data bag item..')
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # delete the rds instance
        terminated = False
        id = 'undefined'
        try:
            id = item['id']
            self.cloudapi.delete_rds_instance(id)
            terminated = True
            self.log.info('Deleted rds instance %s' % id)
        except Exception, e:
            self.log.warn('Error deleting rds instance %s:\n%s' % (id,str(e)))
        
        # delete item from chef
        item.delete()
        self.log.info('Deleted data bag item %s/%s' % (self.name,id))
        
        # show the grid
        if terminated:
            add_notice(req, _('%(label)s %(id)s has been deleted.',
                              label=self.label, id=id))
        else:
            add_warning(req,
                _("%(label)s %(id)s was not terminated as expected, " + \
                  "but its chef data bag item was deleted. " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=id))
        req.redirect(req.href.cloud(self.name))
        
    def audit(self, req, id):
        req.perm.require('CLOUD_MODIFY')
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','rds_audit.py'))
        self._spawn(req, exe, {}, {})
    