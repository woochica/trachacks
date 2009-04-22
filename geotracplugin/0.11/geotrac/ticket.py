"""
GeoTrac:
a plugin for Trac to geolocate issues
http://trac.edgewall.org
"""

import geopy

from customfieldprovider import ICustomFieldProvider
from trac.config import Option, BoolOption
from trac.core import *
from trac.ticket.api import ITicketManipulator

class GeoTrac(Component):

    implements(ITicketManipulator, ICustomFieldProvider)

    ### configuration options
    mandatory_location = BoolOption('geo', 'mandatory_location', 'false',
                                    "Enforce a mandatory location field")
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


        location = ticket['location'].strip()

        # enforce the location field, if applicable
        if not location:
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
        try:
            address, (lat, lon) = self.geolocate(location)
        except ValueError, e:
            return [('location', 'Invalid location: %s' % location)]

        # update the address from the geocoder
        ticket['location'] = address

        # add the latitude and longitude to the request environ
        req.environ['geolat'] = lat
        req.environ['geolon'] = lon

        return []


    ### geolocation
    
    def geolocate(self, location):

        # use lat, lon if the format fits
        if location.count(',') == 1:
            lat, lon = location.split(',')
            try:
                lat, lon = float(lat), float(lon)
                return location, (lat, lon)
            except ValueError:
                pass

        # get the geocoder
        if self.google_api_key:
            geocoder = geopy.geocoders.Google(self.google_api_key)
        else:
            geocoder = geopy.geocoders.Google()
        return geocoder.geocode(location)
