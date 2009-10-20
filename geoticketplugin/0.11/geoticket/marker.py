from componentdependencies import IRequireComponents
from interface import IMapMarkerStyle
from math import sqrt
from trac.config import IntOption
from trac.core import *

class ConstantSizeMarker(Component):
    """map marker of constant size"""

    implements(IMapMarkerStyle)

    marker_size = IntOption("geo", "constant_marker_size", "6",
                            "constant map marker size")

    def style(self, ticket, **style):
        return {'pointRadius': str(self.marker_size)}

try:
    from tracvote import VoteSystem

    class VoteProportionalMarkers(Component):

        implements(IMapMarkerStyle)

        min_size = IntOption("geo", "min_marker_size", "3",
                             "minimum map marker size")
        max_size = IntOption("geo", "max_marker_size", "16",
                             "maximum map marker size")


        # method for IMapMarkerStyle
        def style(self, ticket, **style):
            votesystem = VoteSystem(self.env)
            votes = votesystem.get_vote_counts('ticket/%s' % ticket.id)[1]
            max_votes = votesystem.get_max_votes('ticket')
            size = self.marker_radius(votes, max_votes)
            return { 'pointRadius': str(int(size)) }

        # method for IRequireComponents
        def requires(self):
            return [ VoteSystem ]

        # method for calculating point size
        def marker_radius(self, votes, max_votes):
            if max_votes == 0:
                return self.min_size
            size = self.min_size ** 2
            size += ((self.max_size ** 2) - size)*((votes/float(max_votes))**2)
            return sqrt(size)
                                            

except ImportError:
    pass
