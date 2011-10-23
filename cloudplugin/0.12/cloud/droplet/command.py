import os
from trac.util.translation import _

from cloud.droplet import Droplet

class Command(Droplet):
    """A Command cloud droplet."""

    def render_view(self, req, id):
        template,data,content_type = Droplet.render_view(self, req, id)
        if id in ('deploy','audit'):
            href = req.href.cloud('env')
            data['message'] = 'To %s, use the respective button in an' % id + \
              ' <a href=\\"%s\\">Environment\\\'s view</a>.' % href
            data['cmd_fields'] = [] # clear command fields
        else:
            button = ('execute',_('Execute %(label)s',label=self.label),{})
            data['buttons'].append(button)
        return template, data, content_type
    
    def _get_data(self, req, id):
        req.perm.require('CLOUD_MODIFY')
        item = self.chefapi.resource(self.crud_resource, id, self.name)
        
        # prepare launch data
        launch_data = {'node_ref_field':self.node_ref_field}
        for field in self.fields.get_list('crud_view', filter=r"(?!cmd_)"):
            field.set_dict(launch_data, req=req)
        launch_data['command_id'] = id
        
        # prepare attributes
        attributes = {}
        for field in self.fields.get_list('crud_new', filter=r"cmd_.*"):
            attributes[field.name] = field.get(item)
            
        exe = os.path.abspath(os.path.join(
                os.path.dirname(__file__),'..','daemon','ec2_command.py'))
        return launch_data, attributes, exe
    
    def execute(self, req, id, args=None):
        launch_data, attributes, exe = self._get_data(req, id)
        self._spawn(req, exe, launch_data, attributes)
