"""
interfaces for the GeoTicket plugin
"""

from trac.core import Interface

### interfaces for map marker customization

class IMapMarkerSize(Interface):
    
    def size(ticket):
        """returns the size of the map marker for the ticket"""

class IMapMarkerColor(Interface):

    def color(ticket):
        """returns hex color of the map marker for the ticket"""
