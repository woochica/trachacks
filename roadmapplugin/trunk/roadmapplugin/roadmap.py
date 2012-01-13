from trac.core import *
from genshi.filters import Transformer
from genshi.builder import tag
from genshi import HTML
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from operator import attrgetter
from trac.util.translation import domain_functions
import pkg_resources
import re

#from trac.ticket.model import *

_, tag_, N_, add_domain = domain_functions('roadmapplugin', '_', 'tag_', 'N_', 'add_domain')


# copied from RoadmapFilterPlugin.py, see https://trac-hacks.org/wiki/RoadmapFilterPlugin
def get_session_key(name):
        return "roadmap.filter.%s" % name
# copied from RoadmapFilterPlugin.py, see https://trac-hacks.org/wiki/RoadmapFilterPlugin
class FilterRoadmap(Component):
    """Filters roadmap milestones.

Mainly copied from [https://trac-hacks.org/wiki/RoadmapFilterPlugin RoadmapFilterPlugin]
and modified a bit.

Thanks to daveappendix """
    implements(IRequestFilter, ITemplateStreamFilter)

    def _session(self, req, name, default):
        return req.session.get(get_session_key(name), default)

    def _setSessionKey(self, req, name, value):
        sessionKey = get_session_key(name)
        req.session[sessionKey] = value
        
    def _getFilter(self, req, name):
        sessionKey = get_session_key(name)
        result = ''
        if req.args.has_key(name):
            result = req.args[name]
            # make value persistent...
            req.session[sessionKey] = result
        elif req.session.has_key(sessionKey):
            # use persistent value...
            result = req.session[sessionKey]
        return result

    def _getCheckbox(self, req, name, default):
        sessionKey = get_session_key(name)
        result = '0'

        if req.args.has_key('user_modification'):
            # User has hit the update button on the form,
            # so update the session data.
            if req.args.has_key(name):
                result = '1'
            if result == '1':
                req.session[sessionKey] = '1'
            else:
                req.session[sessionKey] = '0'
        elif req.session.get(sessionKey, default) == '1':
            result = '1'

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
            inc_milestones = self._getFilter(req, 'inc_milestones')
            exc_milestones = self._getFilter(req, 'exc_milestones')
            show_descriptions = self._getCheckbox(req, 'show_descriptions', '1') == '1'
            
            keys = [u'noduedate',u'completed']
            showkeys = {'noduedate':'hidenoduedate','completed':'showcompleted'}
            if req.args.has_key('user_modification'):
                if req.args.has_key('show'):
                    for key in keys:
                        if key in req.args['show']:
                            self._setSessionKey(req, showkeys[key], '1')
                        else:
                            self._setSessionKey(req, showkeys[key], '0')
                else:
                    for key in keys:
                        self._setSessionKey(req, showkeys[key], '0')              
            else:
                for key in keys:
                    erg =self._session(req, showkeys[key], '0')
                    if erg == '1':
                        data['show'].append(key)
                
            if inc_milestones != '':
                inc_milestones = [m.strip() for m in inc_milestones.split('|')]
                filteredMilestones = []
                filteredStats = []
                for i in range(len(data['milestones'])):
                    m = data['milestones'][i]
                    if self._matchFilter(m.name, inc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats
                
            if exc_milestones != '':
                exc_milestones = [m.strip() for m in exc_milestones.split('|')]
                filteredMilestones = []
                filteredStats = []
                for i in range(len(data['milestones'])):
                    m = data['milestones'][i]
                    if not self._matchFilter(m.name, exc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats

            if not show_descriptions:
                for m in data['milestones']:
                    m.description = ''

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
                         tag.input(type="text",
                                   name=name,
                                   value=self._session(req, name, ''),
                                   style_="width:60%",
                                   title=_('available prefixes: contains: ~, starts with: ^, ends with: $')))

    def _toggleBox(self, req, label, name, default):
        if self._session(req, name, default) == '1':
            checkbox = tag.input(type='checkbox',
                                name=name,
                                value='true',
                                checked='checked')
        else:
            checkbox = tag.input(type='checkbox',
                                name=name,
                                value='true')
        return checkbox + ' ' + tag.label(label, for_=name)

    def _hackedHiddenField(self):
        # Hack: shove a hidden field in so we can tell if the update
        # button has been hit.
        return tag.input(type='hidden',
                         name='user_modification',
                         value='true')

    def _user_field_input(self, req):
        return tag.div(self._hackedHiddenField()
                       + self._toggleBox(req,
                                         _('Show milestone descriptions'),
                                         'show_descriptions',
                                         'true')
                       + tag.br()
                       + self._filterBox(req, _('Filter:  '), "inc_milestones")
#                       + tag.br()
#                       + self._filterBox(req, "Exclude: ", "exc_milestones")
                       )   

class SortRoadMap(Component):
    """Shows another checkbox in roadmap view, 
which allows you to sort milestones in descending order of due date."""
    implements(IRequestFilter, ITemplateStreamFilter)
    
    directions = ['Descending', 'Ascending']
    criterias = ['Name', 'Due']
    
    def __init__(self):
        locale_dir = pkg_resources.resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)
        
    def _comparems(self, m1, m2, sort_crit):
       if sort_crit == self.criterias[0]:
           # the milestone names are divided at the dots to compare (sub)versions            
           v1 = m1.name.upper().split('.')
           v2 = m2.name.upper().split('.')
           depth = 0
           # As long as both have entries and no result so far
           while depth < len(v1) and depth < len(v2):
               # if (sub)version is different
               if v1[depth] != v2[depth]:
                   # Find leading Numbers in both entrys
                   leadnum1 = re.search(r"\A\d+", v1[depth])
                   leadnum2 = re.search(r"\A\d+", v2[depth])
                   if leadnum1 and leadnum2:         
                       if leadnum1 != leadnum2:
                           return int(leadnum1.group(0)) - int(leadnum2.group(0))
                       else:
                           r1 = v1[depth].lstrip(leadnum1.group(0))
                           r2 = v2[depth].lstrip(leadnum2.group(0))
                           return 1 if (r1 > r2) else -1
                   elif leadnum1:
                       return 1
                   elif leadnum2:
                       return -1
                   else: 
                       return 1 if (v1[depth] > v2[depth]) else -1
               # otherwise look in next depth
               depth += 1
           # End of WHILE
               
           # At least one of the arrays ended and all numbers were equal so far
           # milestone with more numbers is bigger
           return len(v1) - len(v2)
       # other criteria not needed. Can be sorted easier by buildin methods  
       else:
           return 0
              
    def pre_process_request(self, req, handler):
        """ overridden from IRequestFilter"""
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        """ overridden from IRequestFilter"""
        if template == 'roadmap.html':
#            sort_desc = self._get_settings(req)
#            sort_desc = self._get_settings(req)
            sort_direct = self._get_settings(req, 'sortdirect', self.directions[0])
            sort_crit = self._get_settings(req, 'sortcrit', self.criterias[0])
            
            milestones = data['milestones']
            sortedmilestones = []
            
            if sort_crit == self.criterias[0]:                
                for m in milestones:
                    if len(sortedmilestones) == 0:
                        sortedmilestones.append(m)
                    else:
                        index = 0
                        inserted = False
                        while not inserted and index < len(sortedmilestones):
                           sm = sortedmilestones[index]
                           if  self._comparems(m, sm, sort_crit) >= 0:
                               sortedmilestones.insert(index, m)
                               inserted = True
                           else:
                               index += 1
                           if inserted:
                               break
                        # All milestonenames were lower so append the milestone
                        if not inserted:
                            sortedmilestones.append(m)
            else:
                ms_with_due = []
                ms_wo_due = []
                for m in milestones:
                    if m.due:
                        ms_with_due.append(m)
                    else:
                        ms_wo_due.append(m)
                stats = data['milestone_stats']
                new_stats = []
                sortedmilestones = sorted(ms_with_due, key=attrgetter('due'))
                sortedmilestones.extend(ms_wo_due)    
            
            if sort_direct == self.directions[1]:
                sortedmilestones.reverse()
                        
            stats = data['milestone_stats']
            new_stats = []
            
            for i, m in enumerate(sortedmilestones):
                for j, om in enumerate(milestones):
                    if m.name == om.name:
                       new_stats.append(stats[j])
                       continue
            data['milestones'] = sortedmilestones
            data['milestone_stats'] = new_stats
        return template, data, content_type
            
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'roadmap.html':
            sortcrit = self._get_settings(req, 'sortcrit', self.criterias[0])
            sortdirect = self._get_settings(req, 'sortdirect', self.directions[0])

            sel = ' selected = "selected"'
            html_str = '<div>' + _('Sort by: ')
            html_str += '<select name="sortcrit">'
            for crit in self.criterias:
                html_str += '<option value ="%s" %s>%s</option>' % (crit, sel if sortcrit == crit else '', _(crit))
            html_str += '</select>'
            html_str += '<select name="sortdirect">'
            for dir in self.directions:
                html_str += '<option value ="%s" %s>%s</option>' % (dir, sel if sortdirect == dir else '', _(dir))
            html_str += '</select></div>'
            html = HTML(html_str)
            filter = Transformer('//form[@id="prefs"]/div[@class="buttons"]')
            return stream | filter.before(html)
        return stream
    
    
    def _get_settings(self, req, name, default):
        sessionKey = get_session_key(name)
        if req.args.has_key('user_modification'):
            # User has hit the update button on the form,
            # so update the session data.
            req.session[sessionKey] = req.args[name]
            return req.args[name]
        elif req.session.has_key(sessionKey):
            return req.session[sessionKey]
        else:
            return default
    
                 
