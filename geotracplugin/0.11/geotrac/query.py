from geotrac.utils import get_column

from trac.core import *

class GeospatialQuery(Component):
    """query based on geographic data"""

    def query_by_radius(self, lat, lon, radius):
        """
        return tickets within a given radius
        """
        query_str = "ST_DISTANCE(st_pointfromtext('POINT(' || geo_lng || ' ' || geo_lat || ')'), ST_PointFromText('POINT(%s %s)')) < %s" % (lon, lat, radius)

        return get_column('ticket_location', 'ticket', where=query_str)
        
    def query_by_polyon(self, lat, lon, polygon_id):
        pass
        # XXX stub
