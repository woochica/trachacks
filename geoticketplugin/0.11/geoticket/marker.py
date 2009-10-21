from componentdependencies import IRequireComponents
from interface import IMapMarkerStyle
from math import sqrt
from trac.config import IntOption
from trac.config import ListOption
from trac.config import Option
from trac.core import *
from utils import colors

class StyleMarkers(Component):
    """apply a static style to the markers"""

    implements(IMapMarkerStyle)

    styles = ListOption('geo', 'static_marker_style', '',
                        doc="static styles to apply to markers")

    def style(self, ticket, req, **style):
        retval = {}
        for s in self.env.config.getlist('geo', 'static_marker_style'):
            key, value = s.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key not in style:
                retval[key] = value
        return retval

class ColorMarkers(Component):
    """color the map markers based on ticket field"""
    field = Option("geo", "color_field", "type",
                   "color the map markers based on this field")

    implements(IMapMarkerStyle)

    def style(self, ticket, req, **style):

        # cache the colordict on the request
        if 'marker_colordict' not in req.environ:
            req.environ['marker_colordict'] = self.colordict(ticket)

        _colordict = req.environ['marker_colordict']
        if ticket[self.field] in _colordict:
            return { 'fillColor': _colordict[ticket[self.field]],
                     'strokeColor': _colordict[ticket[self.field]] }
        return {}


    def colordict(self, ticket):
        for field in ticket.fields:
            if field['name'] == self.field:
                assert 'options' in field
                _colors = colors(len(field['options']), hexcode=True)
                return dict(zip(field['options'], _colors))
                
        raise AssertionError("Ticket field %s not found" % self.field)

try:
    from tracvote import VoteSystem

    class VoteProportionalMarkers(Component):

        implements(IMapMarkerStyle)

        min_size = IntOption("geo", "min_marker_size", "3",
                             "minimum map marker size")
        max_size = IntOption("geo", "max_marker_size", "16",
                             "maximum map marker size")


        # method for IMapMarkerStyle
        def style(self, ticket, req, **style):
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
