# -*- coding: utf-8 -*-

import time

from trac import ticket
from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.util import Markup
from trac.ticket.admin import TicketAdminPanel


class WorklogAdminPanel(TicketAdminPanel):
    _type = 'worklog'
    _label = ('Work Log', 'Work Log')

    def _render_admin_panel(self, req, cat, page, component):
        req.perm.require('TICKET_ADMIN') and req.perm.require('WORK_ADMIN') 

        bools = [ "timingandestimation", "trachoursplugin", "comment",
                  "autostop", "autostopstart", "autoreassignaccept" ]
        
        if req.method == 'POST' and req.args.has_key('update'):
            for yesno in bools:
                if req.args.has_key(yesno):
                    self.config.set(self._type, yesno, True)
                else:
                    self.config.set(self._type, yesno, False)
                roundup = 1
                if req.args.has_key('roundup'):
                    try:
                        if int(req.args.get('roundup')) > 0:
                            roundup = int(req.args.get('roundup'))
                    except:
                        pass
                self.config.set(self._type, 'roundup', roundup)
                
            self.config.save()

        settings = {}
        for yesno in bools:
            if self.config.getbool(self._type, yesno):
                settings[yesno] = 'checked'

        if self.config.getint(self._type, 'roundup'):
            settings['roundup'] = self.config.getint(self._type, 'roundup')
        
        settings['view'] = 'settings'
        return 'worklog_webadminui.html', settings
