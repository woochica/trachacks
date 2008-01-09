
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

    def process_request(self, req):
        messages = []
        def addMessage(s):
            messages.extend([s]);
        if req.method == 'POST':
            pass
        req.hdf["estimate"]={"href":       req.href.Estimate(),
                             "messages":   messages,
                   }
        add_script(req, "Estimate/JsHelper.js")
        add_script(req, "Estimate/Controls.js")
        add_stylesheet(req, "Estimate/estimate.css")
        return 'estimate.cs', 'text/html'

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
