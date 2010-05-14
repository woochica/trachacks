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

    def _sessionKey(self, name):
        return "roadmap.filter.%s" % name

    def _session(self, req, name, default):
        return req.session.get(self._sessionKey(name), default)

    def _getFilter(self, req, name):
        sessionKey= self._sessionKey(name)
        result= ''
        if req.args.has_key(name):
            result= req.args[name]
            # make value persistent...
            req.session[sessionKey]= result
        elif req.session.has_key(sessionKey):
            # use persistent value...
            result= req.session[sessionKey]
        return result

    def _getCheckbox(self, req, name, default):
        sessionKey= self._sessionKey(name)
        result= False

        if req.args.has_key('user_modification'):
            # User has hit the update button on the form,
            # so update the session data.
            if req.args.has_key(name):
                result= True
            if result:
                req.session[sessionKey]= 'true'
            else:
                req.session[sessionKey]= 'false'
        elif req.session.get(sessionKey, default) == 'true':
            result= True

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
            show_descriptions= self._getCheckbox(req, 'show_descriptions', 'true')

            if inc_milestones != '':
                inc_milestones = [m.strip() for m in inc_milestones.split('|')]
                filtered = []
                for m in data['milestones']:
                    if self._matchFilter(m.name, inc_milestones):
                        filtered.append(m)
                data['milestones'] = filtered
                
            if exc_milestones != '':
                exc_milestones = [m.strip() for m in exc_milestones.split('|')]
                filtered = []
                for m in data['milestones']:
                    if not self._matchFilter(m.name, exc_milestones):
                        filtered.append(m)
                data['milestones'] = filtered

            if not show_descriptions:
                for m in data['milestones']:
                    m.description= ''

        return (template, data, content_type)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'roadmap.html':
            # Insert the new field for entering user names
            filter = Transformer('//form[@id="prefs"]/div[@class="buttons"]')
            return stream | filter.before(self._user_field_input(req))
        return stream

    def _filterBox(self, req, label, name):
        return tag.label(label,
                         tag.input(type= "text",
                                   name= name,
                                   value= self._session(req, name, ''),
                                   style_= "width:60%"))

    def _toggleBox(self, req, label, name, default):
        if self._session(req, name, default) == 'true':
            checkbox= tag.input(type= 'checkbox',
                                name= name,
                                value='true',
                                checked='checked')
        else:
            checkbox= tag.input(type= 'checkbox',
                                name= name,
                                value= 'true')
        return checkbox + ' ' + tag.label(label, for_= name)

    def _hackedHiddenField(self):
        # Hack: shove a hidden field in so we can tell if the update
        # button has been hit.
        return tag.input(type= 'hidden',
                         name= 'user_modification',
                         value='true')

    def _user_field_input(self, req):
        return tag.div(self._hackedHiddenField()
                       + self._toggleBox(req,
                                         'Show milestone descriptions',
                                         'show_descriptions',
                                         'true')
                       + tag.br()
                       + self._filterBox(req, "Include: ", "inc_milestones")
                       + tag.br()
                       + self._filterBox(req, "Exclude: ", "exc_milestones")
                       )                    
