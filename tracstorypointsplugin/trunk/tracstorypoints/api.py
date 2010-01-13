'''
Created on Nov 16, 2009

@author: scott
'''

from datetime import datetime

from trac.ticket import Ticket, ITicketManipulator
from trac.core import *

class TracStoryPointsTicketValidator(Component):
    implements(ITicketManipulator)
    
    def __init__(self):
        pass
    
    def prepare_ticket(req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""
        pass
    
    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        This validates the custom fields from this plugin.
        """
        date_format = '%m/%d/%Y'
        errors = []
        
        # Validate estimated story points field as a valid number or null.
        try:
            if ticket.values['storypoints']:
                ep = float(ticket.values['storypoints'])
        except KeyError:
            self.log.exception('The estimated story points field was not submitted.')
        except ValueError:
            self.log.debug('Value error on trying to add %s as estimated storypoints' % ticket.values['storypoints'])
            errors.append(('Add Estimated Storypoints to Ticket.', 'Value must be a valid number.'))
            
        # Validate completed date field as a valid date or null.
        try:
            # The trac date format seems to be mm/dd/yy but going with 4 digit year.
            if ticket.values['completed']:
                cd = datetime.strptime(ticket.values['completed'], date_format)
        except KeyError:
            self.log.exception('The completed date field was not submitted')
        except ValueError:
            self.log.debug('Value error on trying to add %s as completed date' % ticket.values['completed'])
            errors.append(('Add Completed Date to Ticket', 'Value must be a valid date in format mm/dd/YYYY.'))
            
        return errors