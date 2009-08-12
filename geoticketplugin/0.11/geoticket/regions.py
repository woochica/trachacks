"""
GeoRegions:
a plugin for Trac
http://trac.edgewall.org
"""

import os
import shutil
import subprocess
import tempfile

from pkg_resources import resource_filename
from trac.config import Option
from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_warning
from trac.web.chrome import ITemplateProvider
from tracsqlhelper import get_all_dict

templates_dir = resource_filename(__name__, 'templates')

class GeoRegions(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

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
        if req.perm.has_permission('TRAC_ADMIN'):
            return [ ('geo', 'Geo', 'shapefiles', 'Shapefiles') ]

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
            table = get_all_dict(self.env, "SELECT * FROM georegions")
        except:
            table = None


        if table:
            data['columns'] = table[0].keys()
        else:
            data['columns'] = None

        if not data['columns']:
            add_warning(req, "You have not successfully uploaded any shapefiles.  Please use the upload form.")
        else:
            if self.column not in data['columns']:
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

    ### POST method handlers
    
    def shapefile_upload(self, req):
        """process uploaded shapefiles"""
        files = [ 'shp', 'shx', 'dbf', 'prj' ]

        # sanity check
        for f in files:
            # TODO better error handling
            assert hasattr(req.args[f], 'file')

        # put files in a temporary directory for processing
        tempdir = tempfile.mkdtemp()
        for f in files:
            shapefile = file(os.path.join(tempdir, 'shapefile.%s' % f), 'w')
            print >> shapefile, req.args[f].file.read()
            shapefile.close()
            
        # run pgsql command to get generated SQL
        process = subprocess.Popen(["shp2pgsql", os.path.join(tempdir, 'shapefile'), 'georegions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sql, errors = process.communicate()

        # remove old database if it exists
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
