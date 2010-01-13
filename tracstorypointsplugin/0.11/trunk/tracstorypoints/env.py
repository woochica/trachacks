'''
Handles Environment setup and configuration for the plugin.

    @author: scott turnbull <sturnbu@emory.edu>
    Copyright (C) 2010  Scott Turnbull

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from trac.core import *
from trac.env import IEnvironmentSetupParticipant

class StoryPointSetup(Component):
    """"Creates needed elements for the Story Point Plugin Environment"""
    implements(IEnvironmentSetupParticipant)
     
    def __init__(self):
        """"Setup some of the fields we'll be working with."""
        
        # Setup some commonly reused settings.
        self.section = 'ticket-custom'
        self.sp_options = '|0|0.5|1|2|3|5|8|13|21|34|55'
        
        # Estimated sp field.
        self.storypoints_field = {
                           'storypoints': 'select',
                           'storypoints.label': 'Storypoints',
                           'storypoints.options': self.sp_options,
                           'storypoints.order': 9100,
                           }
           
        # Date task is completed field.
        self.completed_field = {
                                'completed': 'text',
                                'completed.label': 'Date Completed',
                                'completed.order': 9110,
                                }
        
        self.userstory_field = {
                           'userstory': 'text',
                           'userstory.label': 'User Story',
                           'userstory.order': 9120,
                           }
    
        self.custom_fields = [self.storypoints_field, self.completed_field, self.userstory_field]
    
    def environment_created(self):
        # Setup Initial environment
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
        self.log('Trac Story Points Plugin Activated')
    
    def environment_needs_upgrade(self, db):
        """Checks if the environemnt needs and upgrade"""
        return self.fields_need_upgrade()
        
    def upgrade_environment(self, db):
        """Acutually performs the upgrade"""
        self.fields_do_upgrade()
    
    def fields_need_upgrade(self):
        """Checks if the plugin needs and upgrade."""
        for fieldset in self.custom_fields:
            for field in fieldset.keys():
                if not self.config.get(self.section, field):
                    msg = 'Trac Story Point Plugin: Missing %s field.' % field
                    # print msg
                    self.log.error(msg)
                    return True
        return False
    
    def fields_do_upgrade(self):
        """Adds the fields and config changes to the ini file."""
        self.log.info('Trac Story Point Plugin:  Upgrading Fields')
        for fieldset in self.custom_fields:
            # Loop through the defined fields above and create the config for them.
            for k, v in fieldset.items():
                self.config.set(self.section, '%s' % k, '%s' % v)
                self.log.debug('Trac Story Point Plugin: Setting %s to %s' % (k, v))
        self.config.save() # Save the config information.
        
        
class ReportsSetup(Component):
    """This creates the custom reports with story point information"""
    implements(IEnvironmentSetupParticipant)
    
    def environment_created(self):
        """Called when environment if first created"""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
            
    def environment_needs_upgrade(self, db):
        """If reports aren't disabled we wont be able to do custom reporting so this turns it off."""
        if not self.config.get('components', 'trac.ticket.report.*') == 'disabled':
            return True
        return False
    
    def upgrade_environment(self, db):
        """Turns reporting off in favor of custom filtering so reports can be run."""
        self.config.set('components', 'trac.ticket.report.*', 'disabled')
        self.log.info('Trac Story Point Plugin: Disabled reports, use Ticket Query for viewing tickets.')
        self.config.save()
