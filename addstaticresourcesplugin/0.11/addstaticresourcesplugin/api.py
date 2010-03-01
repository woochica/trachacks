import re, os.path
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestFilter
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider, Chrome

srkey = "static_resources"
def urljoin(*args):
  return '/'.join([i.strip('/') for i in args])

class AddStaticResourcesComponent (Component):
  implements (IRequestFilter, ITemplateProvider)
  # IRequestHandler methods
  def pre_process_request(self, req, handler):
    """Called after initial handler selection, and can be used to change
    the selected handler or redirect request.
    
    Always returns the request handler, even if unchanged.
    """
    if(type(handler) == Chrome):
      self.log.debug("AddStaticResourceComponent: skipping, dont futz with other static resources")
      return handler

    self.log.debug("AddStaticResourceComponent: about to add resources, %s ,%s"%(req, handler))
    c = self.env.config
    resources = c.options(srkey)
    for regex, value in resources:
      self.log.debug("AddStaticResourceComponent: Regex:'%s' matched:%s" %(regex,re.search(regex, req.path_info)))
      if re.search(regex, req.path_info):
        paths = c.getlist(srkey, regex)
        for p in paths:
          if p.endswith("js"):
            add_script(req,urljoin(srkey, p))
          elif p.endswith("css"):
            add_stylesheet(req, urljoin(srkey, p))

    return handler

  def post_process_request(self, req, template, data, content_type):
    """Do any post-processing the request might need; typically adding
    values to the template `data` dictionary, or changing template or
    mime type.
    
    `data` may be update in place.
    Always returns a tuple of (template, data, content_type), even if
    unchanged.
    Note that `template`, `data`, `content_type` will be `None` if:
    - called when processing an error page
    - the default request handler did not return any result
    (Since 0.11)
    """
    return (template, data, content_type)

  # ITemplateProvider
  def get_htdocs_dirs(self):
    """Return the absolute path of a directory containing additional
    static resources (such as images, style sheets, etc).
    """
    return [(srkey, resource_filename(__name__, 'htdocs'))]
  
  def get_templates_dirs(self):
    """Return the absolute path of the directory containing the provided
    genshi templates.
    """
    rtn =[]
    try:
      p = resource_filename(__name__, 'templates')
      if os.path.isdir(p):
        rtn.append(p)
    except:
      pass
    return rtn
