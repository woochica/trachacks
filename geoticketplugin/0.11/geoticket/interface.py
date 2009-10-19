"""
interfaces for the GeoTicket plugin
"""

from trac.core import Interface

### interfaces for map marker customization

class IMapMarkerStyle(Interface):

    def style(ticket):
        """returns a dictionary to apply to marker style dictionary"""
