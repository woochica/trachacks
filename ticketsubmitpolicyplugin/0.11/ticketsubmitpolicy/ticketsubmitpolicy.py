"""
TicketSubmitPolicy:
Plugin for trac 0.11
controls ticket submission form via JS
"""

import re

from genshi.builder import tag
from genshi.core import Markup
from genshi.filters import Transformer

from interface import ITicketSubmitPolicy
from pkg_resources import resource_filename

from trac.admin.api import IAdminPanelProvider
from trac.core import Component, ExtensionPoint, implements
from trac.ticket import Ticket
from trac.web import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import ITemplateProvider


def camelCase(string):
    """returns the camelCase representation of a string"""

    args = string.split()
    args = [args[0]] + [ i.capitalize() for i in args[1:] ]
    return ''.join(args)


class TicketSubmitPolicyPlugin(Component):
    """
    enforce a policy for allowing ticket submission based on fields
    """

    implements(ITemplateStreamFilter, IAdminPanelProvider, ITemplateProvider) 
    
    # XXX this should be renamed -> actions
    policies = ExtensionPoint(ITicketSubmitPolicy)

    comparitors = { 'is': 1,
                    'is not': 1,
                    'is in': 'Array',
                    'is not in': 'Array' }

    ### methods for accessing the policies
    # XXX the naming convention for these is horrible

    def policy_dict(self):
        retval = {}
        for policy in self.policies:
            retval[policy.name()] = policy
        return retval

    def save(self, policies):

        # shorthand
        section = 'ticket-submit-policy'
        config = self.env.config

        # remove the old section
        for key, value in config.options(section):
            config.remove(section, key)

        # create new section from policy dictionary
        for policy in policies:
            condition = policies[policy]['condition']
            if condition:
                value = ' && '.join(['%s %s %s' % (i['field'], i['comparitor'], i['value']) for i in condition])
                config.set(section, 
                           '%s.condition' % policy,
                           value)
            for action in policies[policy]['actions']:
                config.set(section,
                           '%s.%s' % (policy, action['name']),
                           ', '.join(action['args']))

        # save the policy
        config.save()

    def parse(self):
        """
        parse the [ticket-submit-policy] section of the config for policy rules
        """

        section = dict([i for i in self.config.options('ticket-submit-policy')])

        def parse_list(string):
            return [ i.strip() for i in string.split(',') if i.strip()] 

        policies = {} 
        for key in section:
            try:
                name, action = key.split('.', 1)
            except ValueError:
                self.log.error('invalid key: %s' % key) # XXX log this better
                continue
            if not policies.has_key(name):
                policies[name] = {}

            if action == 'condition':
                condition = section[key]

                conditions = condition.split('&&')

                for condition in conditions:

                    # look for longest match to prevent substring matching
                    comparitors = self.comparitors.keys()
                    comparitors.sort(key=lambda x: len(x), reverse=True)
                    match = re.match('.* (%s) .*' % '|'.join(comparitors), condition)

                    if match:
                        comparitor = str(match.groups()[0]) # needs to be a str to be JS compatible via repr
                        field, value = [i.strip() for i in condition.split(comparitor, 1)]
                        field = str(field)
                        if self.comparitors[comparitor] == 'Array':
                            value = parse_list(value)

                        else:
                            value = str(value)

                        if 'condition' not in policies[name]:
                            policies[name]['condition'] = []
                        policies[name]['condition'].append(dict(field=field,value=value,comparitor=comparitor))
                            
                    else:
                        self.log.error("Invalid condition: %s" % condition)
                                        
                continue

            if not policies[name].has_key('actions'):
                policies[name]['actions'] = []
            args = parse_list(section[key])
            policies[name]['actions'].append({'name': action, 'args': args})

        for policy in policies:
            # empty condition ==> true
            if not policies[policy].has_key('condition'):
                policies[policy]['condition'] = []

        return policies

    # method for ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'ticket.html':

            # setup variables
            javascript = [self.javascript()]

            onload = []
            onsubmit = []
            policy_dict = self.policy_dict()

            # add JS functions to the head block
            for policy in self.policies:
                policy_javascript = policy.javascript()
                
                if policy_javascript:
                    add_script(req, policy_javascript)
#                    javascript.append(policy_javascript)

            policies = self.parse()
            
            for name, policy in policies.items():

                # insert the condition into the JS
                conditions = policy['condition']
                _conditions = []
                for condition in conditions:
                    _condition = {}
                    _condition['field'] = condition['field']
                    _condition['comparitor'] = camelCase(condition['comparitor'])
                    comp_type =  self.comparitors[condition['comparitor']]
                    value = condition['value']
                    if comp_type == 'Array':
                        _condition['value'] = '[ %s ]' % ', '.join(["'%s'" % v for v in value])
                    else:
                        _condition['value'] = "'%s'" % value
                    _conditions.append("{field: '%(field)s', comparitor: %(comparitor)s, value: %(value)s}" % _condition)
                condition = '%s = [ %s ];' % (name, ', '.join(_conditions))
                javascript.append(condition)

                # find the correct handler for the policy
                for action in policy['actions']:
                    handler =  policy_dict.get(action['name'])
                    if handler is None:
                        self.log.error('No ITicketSubmitPolicy found for "%s"' % action['name'])
                        continue
                
                    # filter the stream
                    stream = handler.filter_stream(stream, name, policy['condition'], *action['args'])


                    # add other necessary JS to the page
                    policy_onload = handler.onload(name, policy['condition'], *action['args'])
                    if policy_onload:
                        onload.append(policy_onload)
                    policy_onsubmit = handler.onsubmit(name, policy['condition'], *action['args'])
                    if policy_onsubmit:
                        onsubmit.append(policy_onsubmit)

            # insert onload, onsubmit hooks if supplied
            if onload:
                javascript.append(self.onload(onload))

            if onsubmit:
                javascript.append(self.onsubmit(onsubmit))
                stream |= Transformer("//form[@id='propertyform']").attr('onsubmit', 'validate()')

            # insert head javascript
            if javascript:
                javascript = '\n%s\n' % '\n'.join(javascript)
                javascript = tag.script(Markup(javascript), **{ "type": "text/javascript"})
                
                stream |= Transformer("head").append(javascript)

        return stream

    ### methods returning JS
    ### TODO: convert these all to templates

    def onload(self, items):
        return """
$(document).ready(function () {
%s
});
""" % '\n'.join(items)


    def onsubmit(self, items):
        """returns text for the onsubmit JS function to be inserted in the head"""
        message = """message = %s
if (message != true)
{
errors[errors.length] = message;
}
"""
        messages = '\n'.join([(message % item) for item in items])

        return """
function validate()
{

var errors = new Array();
%s
if (errors.length)
{

if (errors.length == 1)
{
error_msg = errors[0];
}
else
{
error_msg = errors.join("\\n");
}
alert(error_msg);
return false;

}

return true;
}
""" % messages


    def javascript(self):
        """head javascript required to enforce ticket submission policy"""
        # XXX this should probably go into a separate file

        string = """
function getValue(id)
{
var x=document.getElementById(id);
return x.options[x.selectedIndex].text;
}

function is(x, y)
{
return (x == y);
}

function isNot(x, y)
{
return (x != y);
}

function isIn(x, y)
{
for (index in y)
{

if(x == y[index])
{
return true;
}

}
return false;
}

function isNotIn(x, y)
{
return !isIn(x,y);
}

function condition(policy)
{
    length = policy.length;
    for ( var i=0; i != length; i++ )
        {
            field = getValue('field-' + policy[i].field);
            comparitor = policy[i].comparitor;
            value = policy[i].value;

            if ( !comparitor(field, value) )
                {
                    return false;
                }
        }
    return true;
}

function policytostring(policy)
{
    // this should be replaced by a deCamelCase function
    names = { is: 'is', isNot: 'is not', isIn: 'is in', isNotIn: 'is not in' }

    var strings = new Array(policy.length);
    for ( var i=0; i != policy.length; i++ )
    {
        funcname = names[policy[i].comparitor.name];
        strings[i] = policy[i].field + ' ' + funcname + ' ' + policy[i].value;
    }
    return strings.join(' and ');

}

"""
        return string

    ### methods for IAdminPanelProvider

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if req.perm.has_permission('TRAC_ADMIN'): 
            yield ('ticket', 'Ticket System', 'policy', 'Submit Policy')

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        data = {} # data for template
        data['fields'] = Ticket(self.env).fields # possible ticket fields
        data['comparitors'] = self.comparitors # implemented comparitors
        data['self_actions'] = self.policies # available policies
        data['saved'] = True

        if req.method == 'POST':

            # mark the page as unsaved
            data['saved'] = False

            # organize request args based on policy
            policies = req.args.get('policy', [])
            if isinstance(policies, basestring):
                policies = [ policies ]
            args = dict([(policy, {}) for policy in policies ])
            for arg, value in req.args.items():
                for policy in policies:
                    token = '_%s' % policy
                    if arg.endswith(token):
                        args[policy][arg.rsplit(token, 1)[0]] = value
                
            # get the conditions and policies from the request
            data['policies'] = {}
            for policy in args:
                if 'remove' in args[policy]:
                    continue ### remove this policy
                conditions = {}
                data['policies'][policy] = dict(condition=[], actions=[])
                for field, value in args[policy].items():

                    token = 'condition_'
                    if field.startswith(token):
                        name, index = field.split(token, 1)[1].rsplit('_', 1)
                        index = int(index)
                        if not conditions.has_key(index):
                            conditions[index] = {}
                        conditions[index][name] = value
                        continue

                    token = 'action_'
                    if field.startswith(token):
                        name = field.split(token, 1)[1]
                        if args[policy].get('rm_action_%s' % name, False):
                            continue

                        if isinstance(value, basestring):      
                            value = [ value ]
                        data['policies'][policy]['actions'].append(dict(name=name, args=value))
                        
                # added action
                new_action =  args[policy].get('add_action')
                if new_action:
                    data['policies'][policy]['actions'].append(dict(name=new_action, args=[]))

                for index in sorted(conditions.keys()):
                    if 'rm_condition_%s' % index not in args[policy]:
                        data['policies'][policy]['condition'].append(conditions[index])


            # added conditions
            new_conditions = [ i.split('add_condition_', 1)[-1] 
                               for i in req.args.keys() 
                               if i.startswith('add_condition_') ]
            for name in new_conditions:
                data['policies'][name]['condition'].append(dict(comparitor='', field='', value=''))


            # added policy
            new_policy = req.args.get('new-policy')
            if new_policy:
                data['policies'][new_policy] = dict(actions=[], condition=[])

            # save the data if the user clicks apply
            if 'apply' in req.args:
                self.save(data['policies'])
                data['saved'] = True

        data['current_policy'] = '[ticket-submit-policy]\n%s' % '\n'.join(['%s = %s' % val for val in self.env.config.options('ticket-submit-policy')])
        if req.method == 'GET' or 'apply' in req.args:
            data['policies'] = self.parse() 

        return ('ticketsubmitpolicy.html', data)


    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('ticketsubmitpolicy', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [resource_filename(__name__, 'templates')]
