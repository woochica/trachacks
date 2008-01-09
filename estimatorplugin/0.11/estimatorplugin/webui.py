import re
import dbhelper
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href

class EstimationsPage(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)
    def __init__(self):
        pass

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if re.search('/Estimate', req.path_info):
            return "Estimate"
        else:
            return ""

    def get_navigation_items(self, req):
        url = req.href.Estimate()
        yield 'mainnav', "Estimate", \
              Markup('<a href="%s">%s</a>' %
                     (url , "Estimate"))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/Estimate')

    def load(self, req, addMessage, data):
        try:
            id = int(req.args['id'])
            data["estimate"]["id"] = id
            estimate_rs = dbhelper.get_result_set("SELECT * FROM estimate WHERE estimate_id=%s", id)
            if estimate_rs:
                data["estimate"]["rate"] = estimate_rs.get_value("rate", 0)
                data["estimate"]["variability"] = estimate_rs.get_value("variability", 0)
                data["estimate"]["communication"] = estimate_rs.get_value("communication", 0)
                rs = dbhelper.get_result_set("SELECT * FROM estimate_line_item WHERE estimate_id=%s", id)
                if rs:
                    data["estimate"]["lineItems"] = rs.json_out()
            else:
                addMessage('Cant Find Estimate Id: %s' % id)
        except Exception, e:
            addMessage('Invalid Id: %s' % id)
            addMessage('Error: %s' % e)
        
    def process_request(self, req):
        messages = []
        def addMessage(s):
            messages.extend([s]);
        if req.method == 'POST':
            pass
        data = {}
        data["estimate"]={"href":       req.href.Estimate(),
                          "messages":   messages,
                          "lineItems": '[]',
                          "rate": self.config.get( 'estimator','default_rate') or 200,
                          "variability": self.config.get( 'estimator','default_variability') or 1,
                          "communication": self.config.get( 'estimator','default_communication') or 1,
                          }
        
        if req.args.has_key('id'):
            self.load(req, addMessage, data)


        add_script(req, "Estimate/JSHelper.js")
        add_script(req, "Estimate/Controls.js")
        add_script(req, "Estimate/estimate.js")
        add_stylesheet(req, "Estimate/estimate.css")
        #return 'estimate.cs', 'text/html'
        return 'estimate.html', data, None

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('Estimate', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        genshi templates.
        """
        rtn = [resource_filename(__name__, 'templates')]
        return rtn
