from componentdependencies import IRequireComponents
from default_image import DefaultTicketImage
from trac.config import Option
from trac.core import *
from web_ui import TicketImageHandler

try:
    from geoticket.interface import IMapMarkerStyle

    class MarkerImage(Component):
        """image map marker"""
        
        implements(IMapMarkerStyle, IRequireComponents)

        image_size = Option('geo', 'marker_image_size', 'thumbnail',
                            "size of images for markers")

        # method for IMapMarkerStyle
        def style(self, ticket):
            default_ticket_image = DefaultTicketImage(self.env)
            # TODO : stub

            return {}

        # method for IRequireComponents
        def requires(self):
            return [ TicketImageHandler ]
        
        
except ImportError:
    pass
