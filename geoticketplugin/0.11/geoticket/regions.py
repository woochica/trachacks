"""
GeoRegions:
a plugin for Trac to locate tickets within given spatial regions
http://trac.edgewall.org
"""

import os
import shutil
import subprocess
import tempfile

from componentdependencies import IRequireComponents
from geoticket.ticket import GeoTicket
from pkg_resources import resource_filename
from trac.config import Option
from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_warning
from trac.web.chrome import ITemplateProvider
from tracsqlhelper import get_all_dict
from tracsqlhelper import get_column

templates_dir = resource_filename(__name__, 'templates')

class GeoRegions(Component):

    implements(IAdminPanelProvider, ITemplateProvider, IRequireComponents)

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
            return [ ('geo', 'Geo', 'shapefiles', 'Shapefiles') ]
        return []

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """

        assert req.perm.has_permission('TRAC_ADMIN')
        methods = [ 'shapefile_upload', 'shapefile_label', 'shapefile_delete' ]

        # process posted data
        if req.method == 'POST':
            for method in methods:
                if method in req.args:
                    getattr(self, method)(req)

        # process data for display
        data = { 'column': self.column,
                 'column_label': self.column_label
                 }
        try:
            table = get_all_dict(self.env, "SELECT * FROM georegions LIMIT 1")
        except:
            table = None

        if table:
            data['columns'] = [ c for c in table[0].keys() if c != 'the_geom' ]
        else:
            data['columns'] = None

        if not data['columns']:
            add_warning(req, "You have not successfully uploaded any shapefiles.  Please use the upload form.")
        elif self.column not in data['columns']:
            add_warning(req, "You have not selected a column for query and display. Please choose a column.")


        # return the template and associated data
        return 'shapefile_admin.html', data
            

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
        db = self.env.get_db_cnx()
        cur = db.cursor()
        cur.execute("DROP TABLE georegions")
        db.commit()

    
    ### internal methods

    def enabled(self):
        """return whether this plugin is functional"""
        try:
            code = subprocess.call(["shp2pgsql"], stdout=subprocess.PIPE)
        except OSError:
            return False
        if code:
            return False
        geoticket = GeoTicket(self.env)
        return geoticket.postgis_enabled()

    def regions(self):
        if self.column:
            return (self.column_label or self.column, get_column(self.env, 'georegions', self.column))


    def tickets_in_region(self, region):
        assert self.column
        the_geom = "SELECT the_geom FROM georegions WHERE %s=%s" % (self.column, region)
        query_str = "ST_CONTAINS((%s), st_pointfromtext('POINT(' || longitude || ' ' || latitude || ')', 4326))" % the_geom
        tickets = get_column(self.env, 'ticket_location', 'ticket',
                             where=query_str)
        assert tickets is not None
        return tickets
