import subprocess

from traclegos.db import PostgreSQL
from traclegos.project import TracProject
from paste.script import templates

var = templates.var

class GeoTracProject(TracProject):
    _template_dir = 'template'
    summary = 'GeoTrac project template'
    db = PostgreSQL
    vars = [ var('basedir', 'base directory for trac',
                 default='.'),
             var('domain', 'domain name where this project is to be served', 
                 default='localhost'),
             ]
    permissions = { 'anonymous': ['TAGS_VIEW'],
                    'authenticated': ['TAGS_VIEW'], }

    def post(self, command, output_dir, vars):
        """
        install PostGIS on the PostgreSQL db;
        see http://postgis.refractions.net/documentation/manual-1.3/ch02.html
        """

        TracProject.post(self, command, output_dir, vars)

        # needed .sql files
        postgis_files = { 'lwpostgis.sql': None, 
                          'spatial_ref_sys.sql': None }
        
        # ensure `locate` is available
        if subprocess.call(['locate', '--help'], stdout=subprocess.PIPE):
            print "locate not available and sadly that seems to be the only way to locate the PostGIS .sql files: %s" % ', '.join(postgis_files.keys())
            return

        # locate the needed PostGIS .sql files
        # if they exist and can't be found with locate, 
        # the locate db may need to be updated:
        # `updatedb`
        for f in postgis_files:
            process = subprocess.Popen(['locate', f], stdout=subprocess.PIPE)
            files, stderr = process.communicate()
            files = files.strip().split('\n')
            if not len(files):
                print '"%s" could not be located (needed for PostGIS)' % f
                return
            if len(files) != 1:
                print 'Multiple file found for "%s":\n %s' % (f, '\n'.join(files))
                return
            postgis_files[f] = files[0]

        # ensure createlang is available
        if subprocess.call(['createlang', '--help'], stdout=subprocess.PIPE):
            print "Error: createlang executable could not be found"
            return
        
        # setup the DB with PostGIS
        db = PostgreSQL.prefix + vars['project']
        commands = [ ['createlang', '--username', vars['database_admin'], 'plpgsql', db] ]
        commands.extend([ [ 'psql', '-d', db, '--username', vars['database_admin'], '-f', postgis_files[f]] 
                          for f in postgis_files])
        for command in commands:
            if subprocess.call(command, stdout=subprocess.PIPE):
                print 'Error calling command: %s' % ' '.join(command)
                return
