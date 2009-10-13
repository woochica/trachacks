"""
DefaultTicketImage:
a plugin for Trac to store the default image in the database
http://trac.edgewall.org
"""

from componentdependencies import IRequireComponents
from imagetrac.image import ImageTrac
from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from tracsqlhelper import create_table
from tracsqlhelper import execute_non_query
from tracsqlhelper import get_scalar
from tracsqlhelper import insert_update


class DefaultTicketImage(Component):
    """
    store the default ticket image in a database
    """

    implements(IEnvironmentSetupParticipant, IRequireComponents)

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM default_image")
            return False
        except:
            return True

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        self.create_db()

    ### method for IRequireComponents
        
    def requires(self):
        return [ ImageTrac ]

    ### internal methods

    def create_db(self):
        default_image = Table('default_image', key=('ticket',))[
            Column('ticket', type='int'),
            Column('image'),
            ]

        create_table(self.env, default_image)
                              
    def default_image(self, ticket_id, size=None):
        image = get_scalar(self.env, "SELECT image FROM default_image WHERE ticket=%s" % ticket_id)
        imagetrac = ImageTrac(self.env)
        images = imagetrac.images(ticket_id)
        if image:
            if size and size in images[image]:
                return image # set default image

        # find an image that works
        for i in images:
            if size:
                if size in images[i]:
                    return i
            else:
                return i

    def set_default(self, ticket_id, image):
        insert_update(self.env, 'default_image', 'ticket', ticket_id, dict(image=image))

