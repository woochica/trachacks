"""
GeoRegions:
a plugin for Trac to locate tickets within given spatial regions
http://trac.edgewall.org

Links:

 * http://www.paolocorti.net/2008/05/03/a-day-with-featureserver-2/

"""

import os
import shutil
import subprocess
import tempfile

from componentdependencies import IRequireComponents
from genshi.builder import Markup
from geoticket.ticket import GeoTicket
from pkg_resources import resource_filename
from trac.config import Option
from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.api import IRequestHandler
from trac.web.chrome import add_warning
from trac.web.chrome import ITemplateProvider
from tracsqlhelper import column_repr
from tracsqlhelper import columns
from tracsqlhelper import execute_non_query
from tracsqlhelper import get_all
from tracsqlhelper import get_all_dict
from tracsqlhelper import get_column
from tracsqlhelper import get_scalar

try:
    import ogr
except ImportError:
    ogr = None

templates_dir = resource_filename(__name__, 'templates')

class GeoRegions(Component):

    implements(IAdminPanelProvider, IRequestHandler, ITemplateProvider, IRequireComponents)

    column = Option('geo', 'region-column', '',
                    "Column to use from georegions database table")
    column_label = Option('geo', 'column-label', '',
                          "label for region column")

    ### methods for IAdminPanelProvider

    """
    Extension point interface for adding panels to the web-based
    administration interface.
    """

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if req.perm.has_permission('TRAC_ADMIN') and self.enabled():
            return [ ('geo', 'Geo', 'regions', 'Regions') ]
        return []

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """

        assert req.perm.has_permission('TRAC_ADMIN')
        methods = [ 'shapefile_upload', 'shapefile_label', 'shapefile_delete', 'kml_upload' ]

        # process posted data
        if req.method == 'POST':
            for method in methods:
                if method in req.args:
                    getattr(self, method)(req)

        # process data for display
        data = { 'column': self.column,
                 'column_label': self.column_label,
                 'drivers': self.drivers(),
                 'openlayers_url': self.env.config.get('geo', 'openlayers_url')
                 }
        try:
            table = get_all_dict(self.env, "SELECT * FROM georegions LIMIT 1")
        except:
            table = None

        if table:
            data['columns'] = [ c for c in table[0].keys() if c != 'the_geom' ]
            data['row'] = table[0]
        else:
            data['columns'] = None
            data['row'] = None

        data['srid'] = self.srid()
        data['kml'] = req.href('region.kml')

        if not data['columns']:
            add_warning(req, "You have not successfully uploaded any shapefiles.  Please use the upload form.")
        elif self.column not in data['columns']:
            add_warning(req, "You have not selected a column for query and display. Please choose a column.")


        # return the template and associated data
        return 'regions_admin.html', data


    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        try:
            get_scalar(self.env, "SELECT the_geom FROM georegions LIMIT 1")
        except:
            return False
        return req.path_info.strip('/') == 'region.kml'

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        gids = get_column(self.env, 'georegions', 'gid')
#        gids = [ gid for gid in gids 
#                 if gid in [ int(i) for i in req.args.getlist('gid') ] 
#                 ]
        regions = {}
        georegions_columns = columns(self.env, 'georegions')
        for gid in gids:
            regions[gid] = {}
            regions[gid]['data'] = {}
            _columns = [ column for column in georegions_columns
                         if column not in set(['gid', 'the_geom']) ]
            for column in _columns:
                regions[gid]['data'][column] = get_scalar(self.env, "SELECT %s FROM georegions WHERE gid=%s" % (column, gid))
            regions[gid]['region'] = Markup(get_scalar(self.env, "SELECT ST_AsKML(the_geom) FROM georegions WHERE gid=%s" % gid))

        # filter out non-matching results
        # XXX this is hacky, but I'm not sure how to do this in SQL
        filter = {}
        for key, value in req.args.items():
            if key in georegions_columns:
                filter[key] = value
        for key in regions.keys():
            for _key, _value in filter.items():
                if str(regions[key]['data'][_key]) != _value:
                    del regions[key]
                    break

        return 'region.kml', dict(regions=regions), 'application/vnd.google-earth.kml+xml'
            

    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [ templates_dir ]
    

    ### method for IRequireComponents

    def requires(self):
        return [ GeoTicket ]


    ### POST method handlers

    def kml_upload(self, req):
        """process uploaded KML files"""

        # sanity check
        if not hasattr(req.args['kml'], 'file'):
            add_warning(req, "Please specify a KML file")
            return

        # generate PostGIS SQL from the KML
        sql = self.kml2pgsql(req.args['kml'].file.read())

        # remove old table if it exists
        try:
            table = get_all_dict(self.env, "SELECT * FROM georegions")
        except:
            table = None
        if table:
            self.shapefile_delete(req)

        # load the SQL in the DB
        db = self.env.get_db_cnx()
        cur = db.cursor()
        cur.execute(sql)
        db.commit()
        
    def shapefile_upload(self, req):
        """process uploaded shapefiles"""

        files = [ 'shp', 'shx', 'dbf', ]
        errors = False

        # sanity check
        for f in files:
            if not hasattr(req.args[f], 'file'):
                add_warning(req, "Please specify a %s file" % f)
                errors = True
        try:
            srid = int(req.args['srid'])
            if srid < 1:
                raise ValueError
        except ValueError:
            add_warning(req, "Please specify an SRID integer")
            errors = True
        if errors:
            return

        # put files in a temporary directory for processing
        tempdir = tempfile.mkdtemp()
        for f in files:
            shapefile = file(os.path.join(tempdir, 'shapefile.%s' % f), 'w')
            print >> shapefile, req.args[f].file.read()
            shapefile.close()
            
        # run pgsql command to get generated SQL
        process = subprocess.Popen(["shp2pgsql", "-s", str(srid), "-g", "the_geom", os.path.join(tempdir, 'shapefile'), 'georegions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sql, errors = process.communicate()

        # remove old table if it exists
        try:
            table = get_all_dict(self.env, "SELECT * FROM georegions")
        except:
            table = None
        if table:
            self.shapefile_delete(req)

        # load the SQL in the DB
        db = self.env.get_db_cnx()
        cur = db.cursor()
        cur.execute(sql)
        db.commit()

        # cleanup temporary directory
        shutil.rmtree(tempdir)

    def shapefile_label(self, req):
        """choose column from shapefiles and set label"""
        column_label = req.args['column_label'].strip()
        self.env.config.set('geo', 'column-label', column_label)
        if 'column' in req.args:
            self.env.config.set('geo', 'region-column', req.args['column'])
        self.env.config.save()

    def shapefile_delete(self, req):
        """remove shapefile database"""
        execute_non_query(self.env, "DROP TABLE georegions")
        execute_non_query(self.env, "DELETE FROM geometry_columns WHERE f_table_name='georegions'")

    
    ### internal methods

    def enabled(self):
        """return whether this plugin is functional"""

        # ensure PostGIS is enabled on the DB
        geoticket = GeoTicket(self.env)
        if not geoticket.postgis_enabled():
            return False

        # check for available drivers
        drivers = self.drivers()
        return bool(drivers)

    def drivers(self):
        """available regions drivers"""
        
        drivers = set([])
        
        # shapefile driver
        try:
            code = subprocess.call(["shp2pgsql"], stdout=subprocess.PIPE)
            if not code:
                drivers.add('shapefile')
        except OSError:
            pass

        # KML driver -- disable for now
#        if hasattr(self, 'kml'):
#            drivers.add('KML')

        return drivers
    

    def regions(self):
        if self.column:
            return (self.column_label or self.column, get_column(self.env, 'georegions', self.column))


    def tickets_in_region(self, region):
        assert self.column
        srid = self.srid()
        assert srid is not None
        the_geom = "SELECT the_geom FROM georegions WHERE %s=%s" % (self.column, column_repr(self.env, 'georegions', self.column, region))
        if srid != 4326:
            the_geom = 'ST_TRANSFORM((%s), 4326)' % the_geom
        query_str = "ST_CONTAINS((%s), st_pointfromtext('POINT(' || longitude || ' ' || latitude || ')', 4326))" % the_geom
        tickets = get_column(self.env, 'ticket_location', 'ticket', where=query_str)
        assert tickets is not None
        return tickets

    def srid(self):
        """returns the SRID of the region"""
        try:
            return get_scalar(self.env, "SELECT srid FROM geometry_columns WHERE f_table_name='georegions'")
        except:
            return None

    if ogr:
        try:
            kml = ogr.GetDriverByName('KML')
            def kml2pgsql(self, kml):
                """insert kml into the georegions db"""

                # make a temporary file for no reason
                handle, name = tempfile.mkstemp(suffix='.kml')
                os.write(handle, kml)
                os.close(handle)

                import pdb; pdb.set_trace()                
                
                pgdriver = ogr.GetDriverByName('PostgreSQL')

        except ogr.OGRError:
            pass
