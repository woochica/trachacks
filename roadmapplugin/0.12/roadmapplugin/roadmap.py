from trac.core import *
from genshi.filters import Transformer
from genshi.builder import tag
from genshi import HTML
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from operator import attrgetter
from trac.util.translation import domain_functions
import pkg_resources

#from trac.ticket.model import *

_, tag_, N_, add_domain = domain_functions('roadmapplugin',  '_', 'tag_', 'N_', 'add_domain')


# copied from RoadmapFilterPlugin.py, see https://trac-hacks.org/wiki/RoadmapFilterPlugin
def get_session_key(name):
        return "roadmap.filter.%s" % name

class SortRoadMap(Component):
    """Shows another checkbox in roadmap view, 
which allows you to sort milestones in descending order of due date."""
    implements(IRequestFilter, ITemplateStreamFilter)
    
    def __init__(self):
        locale_dir = pkg_resources.resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)
        
    def pre_process_request(self, req, handler):
        """ overridden from IRequestFilter"""
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        """ overridden from IRequestFilter"""
        if template == 'roadmap.html':
            sort_desc = self._get_sorting(req)
            
            if sort_desc == 'on':
                milestones = data['milestones']
                ms_with_due = []
                ms_wo_due = []
                for m in milestones:
                    if m.due:
                        ms_with_due.append(m)
                    else:
                        ms_wo_due.append(m)
                stats = data['milestone_stats']
                new_stats = []
                new_milestones = sorted(ms_with_due, key=attrgetter('due'), reverse=True)
                new_milestones.extend(ms_wo_due)
                
                for i, m in enumerate(new_milestones):
                    for j, om in enumerate(milestones):
                        if m.name == om.name:
                           new_stats.append(stats[j])
                           continue
                data['milestones'] = new_milestones
                data['milestone_stats'] = new_stats
                #milestones.sort(key=due) 
        return template, data, content_type

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'roadmap.html':
            sort_desc = self._get_sorting(req)
            html_str = '<div><input type="checkbox" name="sortdesc"'
            if sort_desc == 'on':
                html_str += ' checked'
            html_str += '/> ' + _('Sort descending') + '</div>'
            html = HTML(html_str)
            filter = Transformer('//form[@id="prefs"]/div[@class="buttons"]')
            return stream | filter.before(html)
        return stream
    
    
    def _get_sorting(self, req):
        sessionKey = get_session_key('sortDesc')
        sort_desc= ''
        if req.args.has_key('sortdesc'):
            sort_desc= req.args['sortdesc']
            # make value persistent...
            req.session[sessionKey]= sort_desc
        elif req.session.has_key(sessionKey):
            # use persistent value...
            sort_descresult= req.session[sessionKey]
        return sort_desc
    
# copied from RoadmapFilterPlugin.py, see https://trac-hacks.org/wiki/RoadmapFilterPlugin
class FilterRoadmap(Component):
    """Filters roadmap milestones.

Mainly copied from [https://trac-hacks.org/wiki/RoadmapFilterPlugin RoadmapFilterPlugin]
and modified a bit.

Thanks to daveappendix """
    implements(IRequestFilter, ITemplateStreamFilter)

    def _session(self, req, name, default):
        return req.session.get(get_session_key(name), default)

    def _getFilter(self, req, name):
        sessionKey = get_session_key(name)
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
        sessionKey= get_session_key(name)
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
                filteredMilestones = []
                filteredStats= []
                for i in range(len(data['milestones'])):
                    m= data['milestones'][i]
                    if self._matchFilter(m.name, inc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats
                
            if exc_milestones != '':
                exc_milestones = [m.strip() for m in exc_milestones.split('|')]
                filteredMilestones = []
                filteredStats= []
                for i in range(len(data['milestones'])):
                    m= data['milestones'][i]
                    if not self._matchFilter(m.name, exc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats

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
                                   style_= "width:60%",
                                   title = _('available prefixes: contains: ~, starts with: ^, ends with: $') ))

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
                                         _('Show milestone descriptions'),
                                         'show_descriptions',
                                         'true')
                       + tag.br()
                       + self._filterBox(req, _('Filter: '), "inc_milestones")
#                       + tag.br()
#                       + self._filterBox(req, "Exclude: ", "exc_milestones")
                       )                    
