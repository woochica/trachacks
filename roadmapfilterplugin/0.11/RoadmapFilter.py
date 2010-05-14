from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters import Transformer

author = "daveappendix"

class RoadmapFilterPlugin(Component):
    """Filters roadmap milestones.
    """
    implements(IRequestFilter, ITemplateStreamFilter)

    def _getFilter(self, req, name):
        sessionKey= "roadmap.filter.%s" % name
        result= ''
        if (req.args.has_key(name)):
            result= req.args[name]
            # make value persistent...
            req.session[sessionKey]= result
        elif (req.session.has_key(sessionKey)):
            # use persistent value...
            result= req.session[sessionKey]
        return result

    def _matchFilter(self, name, filters):
        # Existing Trac convention says that the following prefixes
        # on the filter do different things:
        #   ~  - contains
        #   ^  - starts with
        #   $  = ends with
        for filter in filters:
            if filter.startswith('^'):
                if name.startswith(filter[1:]):
                    return True
            elif filter.startswith('$'):
                if name.endswith(filter[1:]):
                    return True
            elif filter.startswith('~'):
                if name.find(filter[1:]) >= 0:
                    return True
            elif name == filter:
                return True
        return False

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'roadmap.html':
            inc_milestones= self._getFilter(req, 'inc_milestones')
            exc_milestones= self._getFilter(req, 'exc_milestones')

            if (inc_milestones != ''):
                # use defined filter... 
                inc_milestones = [m.strip() for m in inc_milestones.split('|')]
                filtered = []
                for m in data['milestones']:
                    if self._matchFilter(m.name, inc_milestones):
                        filtered.append(m)
                data['milestones'] = filtered
                
            if (exc_milestones != ''):
                # use defined filter... 
                exc_milestones = [m.strip() for m in exc_milestones.split('|')]
                filtered = []
                for m in data['milestones']:
                    if not self._matchFilter(m.name, exc_milestones):
                        filtered.append(m)
                data['milestones'] = filtered
                
        return (template, data, content_type)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'roadmap.html':
            # Insert the new field for entering user names
            filter = Transformer('//form[@id="prefs"]/div[@class="buttons"]')
            return stream | filter.before(self._user_field_input(req))
        return stream

    def _user_field_input(self, req):
        return tag.div(tag.label("Include: ",
                                 tag.input(type="text",
                                           name="inc_milestones",
                                           value=req.session.get('roadmap.filter.inc_milestones',''),
                                           style_="width:60%"
                                          )
                                )
                       +
                       tag.br()
                       +
                       tag.label("Exclude: ",
                                 tag.input(type="text",
                                           name="exc_milestones",
                                           value=req.session.get('roadmap.filter.exc_milestones',''),
                                           style_="width:60%"
                                          )
                                )
                      )                    
