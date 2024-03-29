# Narcissus plugin for Trac

from settings import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class NarcissusPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'narcissus'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/configure'

    def process_request(self, req):
        req.hdf['trac.href.narcissus'] = self.env.href.narcissus()
        req.hdf['trac.href.configure'] = self.env.href.configure()
        req.hdf['trac.href.user_guide'] = self.env.href.user_guide()

        req.hdf['main'] = "no"
        req.hdf['config'] = "yes"
        req.hdf['user_guide'] = "no"
        
        self.db = self.env.get_db_cnx()
        cursor = self.db.cursor()
        self._settings = NarcissusSettings(self.db)

        # make updates if requested (and valid)
        if req.args.has_key('add'):
            member = req.args.get('add')
            sql = "insert into narcissus_settings values ('member', '%s')" % member
            cursor.execute(sql)
        if req.args.has_key('remove'):
            member = req.args.get('remove')
            sql = "delete from narcissus_settings where value = '%s'" % member
            cursor.execute(sql)
        if req.args.has_key('bounds'):
            for b in self._settings.bounds:
                try:
                    thresh_a = max(0, int(req.args.get('%s.0' % b)))
                    thresh_b = max(0, int(req.args.get('%s.1' % b)))
                    thresh_c = max(0, int(req.args.get('%s.2' % b)))
                except ValueError:
                    thresh_a, thresh_b, thresh_c = self._settings.bounds[b]
                if thresh_a < thresh_b < thresh_c:
                    for i, thresh in enumerate([thresh_a, thresh_b, thresh_c]):
                        sql = '''update narcissus_bounds set threshold = %s where 
                            resource = "%s" and level = %s''' % (thresh, b, i + 1)
                        cursor.execute(sql)
                        self._settings.bounds[b][i] = thresh
        if req.args.has_key('credits'):
            for c in self._settings.credits:
                try:
                    new_credit = max(0, int(req.args.get(c)))
                except ValueError:
                    new_credit = old_credit
                sql = "update narcissus_credits set credit = %s where type = '%s'"\
                    % (new_credit, c)
                cursor.execute(sql)
                self._settings.credits[c] = new_credit
        self.db.commit()
        
        # refresh/populate configuration fields
        self._settings = NarcissusSettings(self.db)
        for u, _, _ in self.env.get_known_users():
            if u not in self._settings.members:
                req.hdf['user.%s' % u] = u
        
        for m in self._settings.members:
            req.hdf['member.%s' % m] = m

        for b in self._settings.bounds:
            for i, threshold in enumerate(self._settings.bounds[b]):
                req.hdf['bound.%s.%s' % (b, i)] = threshold
        
        for c in self._settings.credits:
            req.hdf['credit.%s' % c] = self._settings.credits[c]

        return 'configure.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('nar', resource_filename(__name__, 'htdocs'))]
