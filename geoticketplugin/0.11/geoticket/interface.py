"""
interfaces for the GeoTicket plugin
"""

from trac.core import Interface

### interface for map marker customization

class IMapMarkerStyle(Interface):

    def style(ticket, req, **style):
        """returns a dictionary to apply to marker style dictionary"""
