from interface import IMapMarkerStyle

from trac.config import IntOption
from trac.core import *

class ConstantSizeMarker(Component):
    """map marker of constant size"""

    implements(IMapMarkerStyle)

    marker_size = IntOption("geo", "constant_marker_size", "6",
                            "constant map marker size")

    def style(self, ticket):
        return {'pointRadius': str(self.marker_size)}
