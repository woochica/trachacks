# Ainsley Lawson.  ainsley.lawson@utoronto.ca
# August 2009

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.query import Query
from trac.util import Markup
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler

from getdata import *
from dbanalysis import *
from suggestedcontact import *
import codebrowser

from genshi import HTML
from genshi.builder import tag
from genshi.filters.transform import Transformer


class SocialNetworkPlugin(Component):
    implements(INavigationContributor, IRequestHandler,
               ITemplateProvider, ITemplateStreamFilter,
               IEnvironmentSetupParticipant)

    # ##################### INavigationContributor ############################
    # ############### Puts a new tab in the navigation bar ####################
    def get_active_navigation_item(self, req):
        return 'socialnetwork'

    def get_navigation_items(self, req):
        yield 'mainnav', 'socialnetwork', \
              Markup('<a href="%s">tracSNAP</a>' % \
                     ( self.env.href.socialnetwork() ))

    # ######################### ITemplateProvider #############################
    # ############ Tell trac where the templates and scripts are ##############
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('socialnetwork', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ################### IEnvironmentSetupParticipant ########################
    # ######## Make the appropriate changes to the database schema ############
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()

        try: # test to see if the appropriate tables exist
            cursor.execute("SELECT count(*) FROM code_relations")
            result = cursor.fetchone()

            cursor.execute("SELECT count(*) FROM expertise")
            result = cursor.fetchone()

            cursor.execute("SELECT count(*) FROM socialnetworkdb_data")
            result = cursor.fetchone()

            cursor.execute("SELECT count(*) FROM social_relations")
            result = cursor.fetchone()

            cursor.execute("SELECT count(*) FROM num_changes")
            result = cursor.fetchone()

            return False

        except: # tables missing; need to upgrade environment
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _upgrade_db(self, db):
        try:
        # Create the tables required for tracSNAP
            cursor = db.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS code_relations ('
                           'file1     TEXT,'
                           'file2     TEXT,'
                           'strength  INTEGER'
                           ')')
            cursor.execute('CREATE TABLE IF NOT EXISTS expertise ('
                           'path      TEXT,'
                           'author    TEXT,'
                           'strength  INTEGER'
                           ')')
            cursor.execute('CREATE TABLE IF NOT EXISTS socialnetworkdb_data ('
                           'name      TEXT,'
                           'value     INTEGER'
                           ')')
            cursor.execute('CREATE TABLE IF NOT EXISTS social_relations ('
                           'person1   TEXT,'
                           'person2   TEXT,'
                           'strength  INTEGER'
                           ')')
            cursor.execute('DELETE FROM socialnetworkdb_data')
            cursor.execute('INSERT INTO socialnetworkdb_data \
                            VALUES ("lastRev", 0)')
            cursor.execute('INSERT INTO socialnetworkdb_data \
                            VALUES ("lastRevTime",0)')
            cursor.execute('DROP VIEW IF EXISTS num_changes')
            cursor.execute('CREATE VIEW num_changes AS \
                            SELECT r.rev AS rev, COUNT(n.path) AS num \
                            FROM revision r, node_change n \
                            WHERE r.rev = n.rev \
                            AND n.node_type != "D"  \
                            GROUP BY r.rev')
            db.commit()

        except Exception, e:
            self.log.error("SocialNetworkPlugin Exception: %s" % (e,));
            db.rollback()

        db.close()


    # ######################### IRequestHandler ###############################
    # ######## Tell Trac what templates to load depending on the path #########

    def match_request(self, req):
        """ Return true when on a tracSNAP page	"""
        return req.path_info == '/socialnetwork' \
                   or req.path_info.startswith('/sn_') \
            or req.path_info.find('/browser/') != -1

    def process_request(self, req):
        """ Load the appropriate template """

        # tracSNAP home
        if req.path_info == '/socialnetwork':
            return 'socialnetwork.html', {}, None

        # Graph templates
        elif req.path_info == '/sn_my_files':
            return 'my_files.html', {}, None
        elif req.path_info == '/sn_overall_files':
            return 'overall_files.html', {}, None
        elif req.path_info == '/sn_my_social':
            return 'my_social_graph.html', {}, None
        elif req.path_info == '/sn_overall_social':
            return 'overall_social_graph.html', {}, None
        elif req.path_info == '/sn_linkto':
            return 'linkto.html', {}, None

        # Data templates
        elif req.path_info == '/sn_my_files_data':
            return 'flare_data.html', {}, None
        elif req.path_info == '/sn_overall_files_data':
            return 'flare_data.html', {}, None
        elif req.path_info == '/sn_my_social_data':
            return 'flare_data.html', {}, None
        elif req.path_info == '/sn_overall_social_data':
            return 'flare_data.html', {}, None
        elif req.path_info == '/sn_linkto_data':
            return 'flare_data.html', {}, None

        # Fullscreen Graph Templates
        elif req.path_info == '/sn_fs_my_files':
            return 'fullscreen_graph.html', {}, None
        elif req.path_info == '/sn_fs_overall_files':
            return 'fullscreen_graph.html', {}, None
        elif req.path_info == '/sn_fs_my_social':
            return 'fullscreen_graph.html', {}, None
        elif req.path_info == '/sn_fs_overall_social':
            return 'fullscreen_graph.html', {}, None

        # Code Browser
        elif req.path.info / find('/browser/') != -1:
            return None, {}, None

    # ####################### ITemplateStreamFilter ###########################
    # ################# Add content to the template page ######################
    def filter_stream(self, req, method, filename, stream, data):

        if req.path_info == '/socialnetwork':
            # ############################################################### #
            # ------------------- TracSNAP home page --------------------------
            # ############################################################### #

            # Get the repository
            repo = self.env.get_repository(req.authname)

            # Clear the tables of data we've analyzed (should be commented out)
            #     clear_tables(self)

            # Analyze the repository!
            determine_relations(self, repo)

            # Make a social recommendation
            rec = make_recommendation_box(self, req.authname, req.base_path)

            # Get the files recently edited by this user
            recent = get_recent_files(self, req.authname, req.base_path)

            return stream \
                   | Transformer('//div[@id="suggested_contact"]').prepend(rec) \
                   | Transformer('//div[@id="recent_files"]').append(recent)



        elif req.path_info == '/sn_my_files':
            # ############################################################### #
            # ----------------------- My Files ------------------------------ #
            # ############################################################### #

            # Check if depth was specified
            query_args = Query.from_string(self.env, req.query_string)
            depth = int(query_args.getfirst("depth", 1))

            # HTML to be inserted into the template
            title = HTML('<h2>My Files</h2>')

            swf = HTML('<object width="600" height="500">\
                    <param name="movie" \
                        value="chrome/socialnetwork/MyFilesGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '\
                        &depth=' + str(depth) + '"> \
                    <embed src="chrome/socialnetwork/MyFilesGraph.swf" \
                        FlashVars="address=' + req.base_path + '\
                        &depth=' + str(depth) + '" \
                        width="600" height="500"></embed> \
                    </object>')

            fs_link = HTML('<a href="sn_fs_my_files?depth='
                           + str(depth) + '">View Full Screen</a>')

            return stream \
                   | Transformer('//div[@id="graph_title"]').prepend(title) \
                   | Transformer('//div[@id="graph"]').prepend(swf) \
                   | Transformer('//div[@id="fs_link"]').prepend(fs_link)



        elif req.path_info == '/sn_overall_files':
            # ############################################################### #
            # --------------------- Overall Files --------------------------- #
            # ############################################################### #

            # Check if subdirectories were specified
            query_args = Query.from_string(self.env, req.query_string)
            subdirs = query_args.getlist("subdirs")
            subdir_vars = '&subdirs='
            if subdirs != []: # Show specified sub-directories
                for d in subdirs:
                    subdir_vars += d + ","
                subdir_vars = subdir_vars[0: len(subdir_vars) - 1]

            # HTML to be inserted into the template
            title = HTML('<h2>Overall Code Relations Graph</h2>')

            swf = HTML('\
                <object width="600" height="500">\
                <param name="movie" \
                    value="chrome/socialnetwork/OverallFilesGraph.swf"> \
                <param name=FlashVars \
                    value="address=' + req.base_path + subdir_vars + '"> \
                <embed src="chrome/socialnetwork/OverallFilesGraph.swf" \
                    FlashVars="address=' + req.base_path + subdir_vars + '" \
                    width="600" height="500"></embed> \
                </object>')


            # Get list of directories to choose from
            repo = self.env.get_repository(req.authname)
            dir_list = get_directory_list(self, repo)

            # Set up query string for fullscreen version
            subdir_vars = ""
            if subdirs != []:
                for d in subdirs:
                    subdir_vars += "&subdirs=" + d
                subdir_vars = "?" + subdir_vars[1: len(subdir_vars)]

            fs_link = HTML('<a href="sn_fs_overall_files'
                           + subdir_vars + '">View Full Screen</a>')

            return stream \
                   | Transformer('//div[@id="graph_title"]').prepend(title) \
                   | Transformer('//div[@id="dir_list"]').prepend(dir_list) \
                   | Transformer('//div[@id="graph"]').prepend(swf) \
                   | Transformer('//div[@id="fs_link"]').prepend(fs_link)



        elif req.path_info == '/sn_my_social':
            # ############################################################### #
            # --------------------- My Social Network ----------------------- #
            # ############################################################### #

            # Check query args to see if there is a graph correction to be made
            query_args = Query.from_string(self.env, req.query_string)
            new_person = query_args.getfirst("person", None)
            if new_person != None:
                strength = query_args.getfirst("strength", 1)
                self.new_social_connection(req.authname, new_person, strength)

            # Check query args for depth
            depth = int(query_args.getfirst("depth", 1))

            # HTML to be inserted into the template
            title = HTML('<h2>My Social Network Graph</h2>')
            drop_down = get_correction_dropdown(self, req.authname)
            swf = HTML('<object width="600" height="500">\
                    <param name="movie" \
                        value="chrome/socialnetwork/MySocialGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '\
                        &depth=' + str(depth) + '"> \
                    <embed src="chrome/socialnetwork/MySocialGraph.swf" \
                        FlashVars="address=' + req.base_path + '\
                        &depth=' + str(depth) + '" \
                        width="600" height="500"></embed> \
                    </object>')

            fs_link = HTML('<a href="sn_fs_my_social?depth='
                           + str(depth) + '">View Full Screen</a>')

            return stream \
                   | Transformer('//div[@id="graph_title"]').prepend(title) \
                   | Transformer('//select[@name="person"]').prepend(drop_down) \
                   | Transformer('//div[@id="graph"]').prepend(swf) \
                   | Transformer('//div[@id="fs_link"]').prepend(fs_link)



        elif req.path_info == '/sn_overall_social':
            # ############################################################### #
            # -------------------- Overall Social Network ------------------- #
            # ############################################################### #

            # HTML to be inserted into the template
            title = HTML('<h2>Overall Social Network Graph</h2>')

            swf = HTML('<object width="600" height="500">\
                    <param name="movie" \
                        value="chrome/socialnetwork/OverallSocialGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '"> \
                    <embed src="chrome/socialnetwork/OverallSocialGraph.swf" \
                        FlashVars="address=' + req.base_path + '" \
                        width="600" height="500"> \
                    </embed> \
                    </object>')

            fs_link = HTML('<a href="sn_fs_overall_social">' +
                           'View Full Screen</a>')

            return stream \
                   | Transformer('//div[@id="graph_title"]').prepend(title) \
                   | Transformer('//div[@id="graph"]').prepend(swf) \
                   | Transformer('//div[@id="fs_link"]').prepend(fs_link)


        elif req.path_info == '/sn_linkto':
            # ############################################################### #
            # ---------------------------- Linkto --------------------------- #
            # ############################################################### #

            # Get the person who we are finding the connection to
            query_args = Query.from_string(self.env, req.query_string)
            them = query_args.getfirst("linkto", "")

            # HTML to be inserted into the template
            title = HTML('<h2>Your Social Link To ' + them + '</h2>')

            swf = HTML('<object width="600" height="500">\
                    <param name="movie" \
                        value="chrome/socialnetwork/Linkto.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '\
                                &linkto=' + them + '"> \
                    <embed src="chrome/socialnetwork/Linkto.swf" \
                        FlashVars="address=' + req.base_path + '\
                                    &linkto=' + them + '" \
                        width="600" height="500"> \
                    </embed> \
                    </object>')

            return stream \
                   | Transformer('//div[@id="graph_title"]').prepend(title) \
                   | Transformer('//div[@id="graph"]').prepend(swf)


        elif req.path_info == '/sn_my_files_data':
        # -----------------------------------------------------------------
            # ---------------------- Data: My Files ---------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            depth = int(query_args.getfirst("depth", 1))

            data = get_my_files_data(self, req.authname, depth)

            return stream \
                   | Transformer('//div[@id="data"]').prepend(data)



        elif req.path_info == '/sn_overall_files_data':
        # -----------------------------------------------------------------
            # ------------------- Data: Overall Files -------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            subdirs = query_args.getlist("subdirs")

            if subdirs[0] == "":
                # Show overall files
                data = get_overall_files_data(self)
            else:
                # Show specified directories
                data = get_subdirs_files_data(self, subdirs)

            return stream \
                   | Transformer('//div[@id="data"]').prepend(data)



        elif req.path_info == '/sn_my_social_data':
        # -----------------------------------------------------------------
            # ---------------------- Data: My Social --------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            depth = int(query_args.getfirst("depth", 1))

            data = get_my_social_data(self, req.authname, depth)
            return stream \
                   | Transformer('//div[@id="data"]').prepend(data)



        elif req.path_info == '/sn_overall_social_data':
            # -----------------------------------------------------------------
            # --------------------- Data: Overall Social ----------------------
            # -----------------------------------------------------------------

            data = get_overall_social_data(self)

            return stream \
                   | Transformer('//div[@id="data"]').prepend(data)


        elif req.path_info == '/sn_linkto_data':
            # -----------------------------------------------------------------
            # ---------------------- Data: Linkto -----------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            them = query_args.getfirst("linkto", "")

            data = get_my_linkto(self, req.authname, them)

            return stream \
                   | Transformer('//div[@id="data"]').prepend(data)


        elif req.path_info == '/sn_fs_my_files':
            # -----------------------------------------------------------------
            # ----------------------- FS My Files -----------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            depth = int(query_args.getfirst("depth", 1))

            swf = HTML('<object width="800" height="800">\
                    <param name="movie" \
                        value="chrome/socialnetwork/MyFilesGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '\
                        &depth=' + str(depth) + '"> \
                    <embed src="chrome/socialnetwork/MyFilesGraph.swf" \
                        FlashVars="address=' + req.base_path + '\
                        &depth=' + str(depth) + '" \
                        width="800" height="800"></embed> \
                    </object>')

            return stream \
                   | Transformer('//div[@id="graph"]').prepend(swf)


        elif req.path_info == '/sn_fs_overall_files':
            # -----------------------------------------------------------------
            # ------------------- FS Overall Files ----------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            subdirs = query_args.getlist("subdirs")
            subdir_vars = '&subdirs='

            if subdirs != []: # Show specified sub-directories
                for d in subdirs:
                    subdir_vars += d + ","
                subdir_vars = subdir_vars[0: len(subdir_vars) - 1]

            swf = HTML('\
                <object width="800" height="800">\
                <param name="movie" \
                    value="chrome/socialnetwork/OverallFilesGraph.swf"> \
                <param name=FlashVars \
                    value="address=' + req.base_path + subdir_vars + '"> \
                <embed src="chrome/socialnetwork/OverallFilesGraph.swf" \
                    FlashVars="address=' + req.base_path + subdir_vars + '" \
                    width="800" height="800"></embed> \
                </object>')

            return stream \
                   | Transformer('//div[@id="graph"]').prepend(swf)

        elif req.path_info == '/sn_fs_my_social':
            # -----------------------------------------------------------------
            # ----------------------- FS My Social ----------------------------
            # -----------------------------------------------------------------

            query_args = Query.from_string(self.env, req.query_string)
            depth = int(query_args.getfirst("depth", 1))

            swf = HTML('<object width="800" height="800">\
                    <param name="movie" \
                        value="chrome/socialnetwork/MySocialGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '\
                        &depth=' + str(depth) + '"> \
                    <embed src="chrome/socialnetwork/MySocialGraph.swf" \
                        FlashVars="address=' + req.base_path + '\
                        &depth=' + str(depth) + '" \
                        width="800" height="800"></embed> \
                    </object>')

            return stream \
                   | Transformer('//div[@id="graph"]').prepend(swf)


        elif req.path_info == '/sn_fs_overall_social':
            # -----------------------------------------------------------------
            # ------------------- FS Overall Social ---------------------------
            # -----------------------------------------------------------------

            swf = HTML('<object width="800" height="800">\
                    <param name="movie" \
                        value="chrome/socialnetwork/OverallSocialGraph.swf"> \
                    <param name=FlashVars \
                        value="address=' + req.base_path + '"> \
                    <embed src="chrome/socialnetwork/OverallSocialGraph.swf" \
                        FlashVars="address=' + req.base_path + '" \
                        width=800 height=800> \
                    </embed> \
                    </object>')

            return stream \
                   | Transformer('//div[@id="graph"]').prepend(swf)

        elif req.path_info.find("/browser/") != -1:
            # -----------------------------------------------------------------
            # ------------------- Related Files and Experts -------------------
            # -----------------------------------------------------------------

            css = codebrowser.get_css(self, req)
            rhtml = codebrowser.related_files_html(self, req)
            ehtml = codebrowser.experts_html(self, req)

            return stream \
                   | Transformer('//div[@id="footer"]').before(rhtml) \
                   | Transformer('//div[@id="footer"]').before(ehtml) \
                   | Transformer('//head').append(css)

        else:
            return stream


