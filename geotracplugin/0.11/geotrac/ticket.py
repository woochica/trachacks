"""
GeoTrac:
a plugin for Trac to geolocate issues
http://trac.edgewall.org
"""

import geopy

from customfieldprovider import ICustomFieldProvider
from geotrac.utils import create_table
from geotrac.utils import execute_non_query
from geotrac.utils import get_all
from geotrac.utils import get_column
from geotrac.utils import get_first_row
from geotrac.utils import get_scalar
from trac.config import Option, BoolOption
from trac.core import *
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import ITicketChangeListener
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket


class GeolocationException(Exception):
    """error for multiple and unfound locations"""
    
    def __init__(self, location='', locations=()):
        Exception.__init__(self, location, locations)
        self.location = location
        self.locations = locations
    
    def __str__(self):
        if self.locations:
            return "Multiple locations found: %s" % '; '.join([i[0] for i in self.locations])
        else:
            if location.strip(): 
                return "%s could not be located" % self.location
            else:
                return "No location"

class GeoTrac(Component):

    implements(ICustomFieldProvider, ITicketManipulator, ITicketChangeListener, IEnvironmentSetupParticipant)

    ### configuration options
    mandatory_location = BoolOption('geo', 'mandatory_location', 'false',
                                    "Enforce a mandatory and valid location field")
    google_api_key = Option('geo', 'google_api_key', '',
                            "Google maps API key, available at http://code.google.com/apis/maps/signup.html")


    ### method for ICustomFieldProvider

    # TODO : ensure CustomFieldProvider is enabled
    def fields(self):
        return { 'location': None }

    ### methods for ITicketManipulator

    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""


        # compare ticket['location'] with stored version for existing tickets
        location_changed = True
        if ticket.id:
            location_changed = not ticket['location'] == Ticket(self.env, ticket.id)['location']


        location = ticket['location'].strip()

        # enforce the location field, if applicable
        if not location:
            if location_changed and ticket.id:
                self.delete_location(ticket.id)
            if self.mandatory_location:
                return [('location', 'Please enter a location')]
            else:
                return []

        # XXX blindly assume UTF-8
        try:
            location = location.encode('utf-8')
        except UnicodeEncodeError:
            raise
        
        # geolocate the address
        # XXX should check on location_changed
        try:
            ticket['location'], (lat, lon) = self.geolocate(location)
            if ticket.id:
                self.set_location(ticket.id, lat, lon)
            
            req.environ['geolat'] = lat
            req.environ['geolon'] = lon
        except GeolocationException, e:
            if location_changed and ticket.id:
                self.delete_location(ticket.id)
            if self.mandatory_location:
                return [('location', str(e))]

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
        # TODO : could cache the geolocation in memory
        # instead of geolocating twice (once here and once in
        # ITicketManipulator)
        try:
            location, (lat, lon) = self.locate_ticket(ticket)
            self.set_location(ticket.id, lat, lon)
        except GeolocationException:
            pass

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        # remove extraneous location data;
        # a new ticket could be made with the same id
        self.delete_location(ticket.id)


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
        return not self.version()

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        ticket_location_table = Table('ticket_location', key='ticket')[
            Column('ticket', type='int'),
            Column('latitude', type='float'),
            Column('longitude', type='float'),
            Index(['ticket'])]
        create_table(self.env, ticket_location_table)
        tickets = get_column(self.env, 'ticket', 'id')
        tickets = [ Ticket(self.env, ticket) for ticket in tickets ]
        for ticket in tickets:
            try:
                location, (lat, lon) = self.locate_ticket(ticket)
                self.set_location(ticket.id, lat, lon)
            except GeolocationException:
                pass

        execute_non_query(self.env, "insert into system (name, value) values ('geotrac.db_version', '1');")

    def version(self):
        """returns version of the database (an int)"""

        version = get_scalar(self.env, "select value from system where name = 'geotrac.db_version';")
        if version:
            return int(version)
        return 0


    ### geolocation
    
    def geolocate(self, location):

        # use lat, lon if the format fits
        if location.count(',') == 1:
            lat, lon = location.split(',')
            try:
                lat, lon = float(lat), float(lon)
                if (-90. < lat < 90.) and (-180. < lon < 180.):
                    return [location, (lat, lon)]
            except ValueError:
                pass

        # get the geocoder
        if self.google_api_key:
            geocoder = geopy.geocoders.Google(self.google_api_key)
        else:
            geocoder = geopy.geocoders.Google()
        locations = list(geocoder.geocode(location, exactly_one=False))
        if len(locations) == 1:
            return locations[0]
        else:
            raise GeolocationException(location, locations)

    def locate_ticket(self, ticket):
        if ticket.id:
            import pdb;  pdb.set_trace() 

        if not ticket['location'].strip():
            raise GeolocationException

        # XXX blindly assume UTF-8
        try:
            location = ticket['location'].encode('utf-8')
        except UnicodeEncodeError:
            raise

        location, (lat, lon) = self.geolocate(location)
        return location, (lat, lon)

    def set_location(self, ticket, lat, lon):
        """
        sets the ticket location in the db
        * ticket: the ticket id (int)
        * lat, lon: the lattitude and longtitude (degrees)
        """

        # determine if we need to insert or update the table
        # (SQL is retarded)
        if get_first_row(self.env, "select ticket from ticket_location where ticket='%s'" % ticket):
            execute_non_query(self.env, "update ticket_location set ticket=%s, latitude=%s, longitude=%s where ticket=%s", ticket, lat, lon, ticket)
        else:
            execute_non_query(self.env, "insert into ticket_location (ticket, latitude, longitude) values (%s, %s, %s)", ticket, lat, lon)
        
    def delete_location(self, ticket):
        """
        deletes a ticket location in the db
        * ticket: the ticket id (int)
        """
        
        if get_first_row(self.env, "select ticket from ticket_location where ticket='%s'" % ticket):
            execute_non_query(self.env, "delete from ticket_location where ticket='%s'" % ticket)
