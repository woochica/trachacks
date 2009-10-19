from interface import IMapMarkerSize

from trac.config import IntOption
from trac.core import *

class ConstantSizeMarker(Component):
    """map marker of constant size"""

    implements(IMapMarkerSize)

    marker_size = IntOption("geo", "constant_marker_size", "6",
                            "constant map marker size")

    def size(self, ticket):
        return self.marker_size
