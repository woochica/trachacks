import os
from trac.util.translation import _

from cloud.droplet import Droplet
from cloud.droplet.command import Command
from cloud.progress import Progress


class Environment(Command):
    """An Environment cloud droplet."""
    
    def render_view(self, req, id):
        template,data,content_type = Droplet.render_view(self, req, id)
        deploy = self._get_command('deploy')
        audit = self._get_command('audit')
        
        if deploy:
            attrs = {}
            progress_file = self._is_deploying(id)
            if progress_file:
                href = req.href.cloud(self.name, action='progress',
                                      file=progress_file)
                data['message'] = '<b>Deploying!</b> Track the %s' % id + \
                  ' deployment <a href=\\"%s\\">here</a>.' % href
                attrs = {'disabled':'disabled'}
            button = ('execute',_('Deploy to %(label)s',label=self.label),attrs)
            data['buttons'].append(button)
            
        if audit:
            button = ('audit',_('Audit %(label)s',label=self.label),{})
            data['buttons'].append(button)
        
        if not deploy and not audit:
            data['cmd_fields'] = []
            
        return template, data, content_type
    
    def _get_command(self, id):
        try:
            return self.chefapi.resource('data', id, 'command')
        except:
            return None
        
    def _is_deploying(self, env):
        """Determines whether there's an active deployment for the given
        environment and if so returns its progress file, else False."""
        deploy_file = '/tmp/deploy-%s' % env
        if not os.path.exists(deploy_file):
            return False
        
        # extract progress file
        f = open(deploy_file,'r')
        progress_file = f.read().strip()
        f.close()
        
        # check if progress file exists
        if not os.path.exists(progress_file):
            return False
        
        # check if done deploying
        if Progress(progress_file).is_done():
            return False
        return progress_file
    
    def _set_deploying(self, env, progress_file):
        """Sets the contents of the given environment's deploy file to
        the given progress file."""
        deploy_file = '/tmp/deploy-%s' % env
        f = open(deploy_file,'w')
        f.write(progress_file)
        f.close()
    
    def execute(self, req, id):
        """Deploy to an environment."""
        launch_data, attributes, exe = self._get_data(req, id)
        launch_data['cmd_environments'] = [attributes['name']]
        launch_data['command_id'] = 'deploy'
        deploy = self._get_command('deploy')
        attributes['command'] = deploy['command']
        progress_file = Progress.get_file()
        self._set_deploying(id, progress_file)
        self._spawn(req, exe, launch_data, attributes, progress_file)
    
    def audit(self, req, id):
        """Audit an environment."""
        launch_data, attributes, exe = self._get_data(req, id)
        launch_data['cmd_environments'] = [attributes['name']]
        launch_data['command_id'] = 'audit'
        audit = self._get_command('audit')
        attributes['command'] = audit['command']
        self._spawn(req, exe, launch_data, attributes)
