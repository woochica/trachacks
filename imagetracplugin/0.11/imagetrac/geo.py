from componentdependencies import IRequireComponents
from default_image import DefaultTicketImage
from image import ImageTrac
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
        def style(self, ticket, **style):
            default_ticket_image = DefaultTicketImage(self.env)
            if default_ticket_image.default_image(ticket.id, self.image_size):
                retval = { 'externalGraphic': self.env.href('ticket', ticket.id, 'image', self.image_size) }
                if 'pointRadius' not in style:
                    imagetrac = ImageTrac(self.env)
                    retval['pointRadius'] = str(int(0.5*max(imagetrac.sizes()[self.image_size])))
                return retval
            return {}

        # method for IRequireComponents
        def requires(self):
            return [ TicketImageHandler ]
        
        
except ImportError:
    pass
