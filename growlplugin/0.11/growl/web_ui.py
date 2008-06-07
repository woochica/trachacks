# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.

from trac.core import *
from trac.perm import IPermissionRequestor, PermissionError
from trac.prefs.api import IPreferencePanelProvider
from trac.web.chrome import add_stylesheet, ITemplateProvider
from growl.notifier import GrowlNotifierSystem


__all__ = ['GrowlPreferencePanel']

class GrowlPreferencePanel(Component):

    implements(ITemplateProvider, 
               IPermissionRequestor,
               IPreferencePanelProvider)
    
    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc)."""
        from pkg_resources import resource_filename
        return [('growl', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates."""
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['GROWL_MODIFY']
        return actions + [('GROWL_ADMIN', actions)]

        
    # IPreferencePanelProvider Interface 

    def get_preference_panels(self, req):
        """Return a list of available preference panels."""
        if not self.env[GrowlNotifierSystem].is_userprefs_enabled():
            self.log.info("Growl: User notifications not enabled")
            return
        if 'GROWL_MODIFY' not in req.perm:
            self.log.info("Growl: User does not have GROWL_MODIFY permission")
            return
        yield('growl', 'Growl Notification')

    def render_preference_panel(self, req, panel):
        """Process a request for a preference panel."""
        notifier = self.env[GrowlNotifierSystem] 
        sources = notifier.get_available_sources()

        if req.method == 'POST':
            if 'GROWL_MODIFY' not in req.perm:
                raise PermissionError("No permission to change Growl settings")
            host = req.args.get('host')
            if notifier.validate_host('GROWL_ADMIN' in req.perm, host):
                req.session['growl.host'] = host
                # send a registration request to the host
                notifier.register_notifications([host])
            if True:
                for source in sources:
                    key = 'growl.source.%s' % source
                    if source in req.args:
                        req.session[key] = '1'
                    elif key in req.session:
                        del req.session[key]
            
            req.redirect(req.href.prefs(panel or None))
    
        data = {}
        data['sources'] = []
        for source in sources:
            label = '%s%s' % (source[0].upper(), source[1:])
            key = 'growl.source.%s' % source
            enabled = req.session.has_key(key) and req.session[key]
            data['sources'].append({'name': source, 'label': label,
                                    'enabled': enabled})
        data['host'] = req.session.has_key('growl.host') and \
                           req.session['growl.host']
        data['settings'] = {'session': req.session }

        # add custom stylesheet
        add_stylesheet(req, 'growl/css/growl.css')
        return 'pref_growl.html', data

    # Implementation
    
    def __init__(self):
        pass
