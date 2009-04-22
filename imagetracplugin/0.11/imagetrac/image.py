"""
ImageTrac:
a plugin for Trac to add images to tickets upon creaton
http://trac.edgewall.org
"""

from PIL import Image

from trac.attachment import Attachment
from trac.config import BoolOption
from trac.core import *
from trac.mimeview import Mimeview
from trac.ticket.api import ITicketChangeListener
from trac.ticket.api import ITicketManipulator
from trac.env import IEnvironmentSetupParticipant


class ImageTrac(Component):

    implements(ITicketManipulator, ITicketChangeListener, IEnvironmentSetupParticipant)

    mandatory_image = BoolOption('ticket', 'mandatory_image', 'false', 
                                 "Enforce a mandatory image for created tickets")

    ### methods for ITicketManipulator

    """Miscellaneous manipulation of ticket workflow features."""

    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        if not ticket.exists:
            image = req.args.get('ticket_image')
            if not hasattr(image, 'fp'):
                if self.mandatory_image:
                    return [('ticket_image', 'Images required for tickets. Please upload an image.')]
                else:
                    return []
            mimeview = Mimeview(self.env)
            mimetype = mimeview.get_mimetype(image.filename)
            if mimetype is None:
                return[('ticket_image', 'Uploaded file is not an image')]
            if mimetype.split('/',1)[0] != 'image':
                return [('ticket_image', 'Uploaded file is not an image, instead it is %s' % mimetype)]
            
            try:
                Image.open(image.file)
            except IOError, e:
                return[('ticket_image', str(e))]

        else:
            return []

        # store the image temporarily
        if not hasattr(self, 'image'):
            self.image = {}
        self.image[ticket['summary']] = req.args['ticket_image']


        return []

    ### methods for ITicketChangeListener

    """Extension point interface for components that require notification
    when tickets are created, modified, or deleted."""

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        image = self.image.pop(ticket['summary'])
        attachment = Attachment(self.env, 'ticket', ticket.id)
        attachment.author = ticket['reporter']
        attachment.description = ticket['summary']
        image.file.seek(0,2) # seek to end of file
        size = image.file.tell()
        image.file.seek(0)
        attachment.insert(image.filename, image.file, size)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""



    ### methods for IEnvironmentSetupParticipant
    ### needed?

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        self.upgrade_environment(self)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        return False

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """


