# Plugin for trac 0.11

import re

from genshi.builder import tag 
from genshi.filters import Transformer

from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider


def camelCase(string):
    """returns the camelCase representation of a string"""

    args = string.split()
    args = [args[0]] + [ i.capitalize() for i in args[1:] ]
    return ''.join(args)


### policies

class ITicketSubmitPolicy(Interface):
    """interface for ticket submission policy enforcers"""

    def name():
        """name of the policy"""

    def filter_stream(stream, field, comparitor, value, *args):
        """filter the stream and return it"""

    def javascript():
        """returns javascript functions"""

    def onload(field, comparitor, value, *args):
        """returns code to be executable on page load"""

    def onsubmit(field, comparitor, value, *args):
        """returns code to be executed on form submission"""

class TicketRequires(Component):
    """bits for requiring a field"""
    implements(ITicketSubmitPolicy)

    def name(self):
        return 'requires'

    def filter_stream(self, stream, field, comparitor, value, requiredfield):
        return stream

    def javascript(self):
        return """
function requires(contingentfield, comparitor, value, requiredfield)
{
var val=getValue("field-" + contingentfield);
var element=document.getElementById("field-" + requiredfield);
var field=getValue("field-" + requiredfield);

if (comparitor(val, value))
{

if (!field)
{
return "Please provide a " + requiredfield + " for this " + contingentfield + " " + value + " ticket";
}

}
else
{
element.value = "";
}

return true;
}
""" 

    def onload(self, field, comparitor, value, *args):
        return

    def onsubmit(self, field, comparitor, value, requiredfield):
        requires = "requires('%s', %s, %s, '%s');" % (field, comparitor, value, requiredfield)
        return requires

### 

class TicketExcludes(Component):
    """bits for exluding field under a condition"""
    implements(ITicketSubmitPolicy)

    def name(self):
        return 'excludes'

    def filter_stream(self, stream, field, comparitor, value, excludedfield):
        exclude = "exclude('%s', %s, %s, '%s')" % ( field, comparitor, value, excludedfield )
        stream |= Transformer("//select[@id='field-%s']" % field).attr('onchange', exclude)
        return stream

    def javascript(self):
        return """function exclude(contingentfield, comparitor, value, excludedfield)
{
var val=getValue("field-" + contingentfield);
var element=document.getElementById("field-" + excludedfield);

if (comparitor(val, value))
{
element.style.display="none";
}
else
{
element.style.display="";
}

}
"""

    def onload(self, field, comparitor, value, excludedfield):
        return "exclude('%s', %s, %s, '%s');" % ( field, comparitor, value, excludedfield )

    def onsubmit(self, field, comparitor, value, excludedfield):
        return


class TicketSubmitPolicyPlugin(Component):
    """
    get the selected option from HTML like this:

<select id="field-type" name="field_type">
<option selected="selected">defect</option><option>enhancement</option><option>task</option>
</select>

Notes to self:
Generalizing this would be:
type == defect -> requires(version)
type != defect -> excludes(version)

Does this work for http://trac.openplans.org/trac/ticket/5 and the confirmed box?

state != resolved -> excludes(confirmed)

So yes, I think
    """

    implements(ITemplateStreamFilter) 
    policies = ExtensionPoint(ITicketSubmitPolicy)

#     comparitors =  {'!=': 'is', 
#                     '==': 'isNot',
#                     'in': 'isIn',
#                     'not in': 'isNotIn' }

    comparitors = { 'is': 1,
                    'is not': 1,
                    'is in': 'Array',
                    'is not in': 'Array' }

    def policy_dict(self):
        retval = {}
        for policy in self.policies:
            retval[policy.name()] = policy
        return retval

    def parse(self):
        """
        parse the [ticket-submit-policy] section of the config for policy rules
        """

        # XXX wtf?
        section = dict([i for i in self.config.options('ticket-submit-policy')])


        policies = {} # XXX this should probably be a real class, not an abused dict
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

                # look for longest match to prevent substring matching
                comparitors = sorted(self.comparitors.keys(), key=lambda x: len(x), reverse=True)
                match = re.match('.* (%s) .*' % '|'.join(comparitors), condition)
                if match:
                    comparitor = match.groups()[0]
                    field, value = [i.strip() for i in condition.split(comparitor, 1)]
                    if self.comparitors[comparitor] == 'Array':
                        value = ', '.join(["'%s'" % i.strip() 
                                           for i in value.split(',')])
                        value = '[%s]' % value
                    else:
                        value = "'%s'" % value
                    comparitor = camelCase(comparitor)
                    policies[name]['condition'] = dict(field=field,value=value,comparitor=comparitor)

                else:
                    self.log.error("Invalid condition: %s" % condition)
                                        
                continue

            if not policies[name].has_key('actions'):
                policies[name]['actions'] = []
            args = [ i.strip() for i in section[key].split(',') if i.strip()]
            policies[name]['actions'].append({'name': action, 'args': args})

        for policy in policies:
            # don't handle empty conditions (yet)
            if not policies[policy].has_key('condition'):
                self.log.error("ticket-submit-policy %s has no condition, removing");
                policies.pop(policy)
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
                    javascript.append(policy_javascript)

            policies = self.parse()
            
            for key, policy in policies.items():

                # condition 
                field = policy['condition']['field']
                comparitor = policy['condition']['comparitor']
                value = policy['condition']['value']

                # find the correct handler for the policy
                for action in policy['actions']:
                    handler =  policy_dict.get(action['name'])
                    if handler is None:
                        self.log.error('No ITicketSubmitPolicy found for "%s"' % action['name'])
                        continue
                
                    # filter the stream
                    stream = handler.filter_stream(stream, field, comparitor, value, *action['args'])


                    # add other necessary JS to the page
                    policy_onload = handler.onload(field, comparitor, value, *action['args'])
                    if policy_onload:
                        onload.append(policy_onload)
                    policy_onsubmit = handler.onsubmit(field, comparitor, value, *action['args'])
                    if policy_onsubmit:
                        onsubmit.append(policy_onsubmit)

            # insert onload, onsubmit hooks if supplied
            if onload:
                javascript.append(self.onload(onload))
                stream |= Transformer("body").attr('onload', 'onload()')
            if onsubmit:
                javascript.append(self.onsubmit(onsubmit))
                stream |= Transformer("//form[@id='propertyform']").attr('onsubmit', 'return onsubmit')

            # insert head javascript
            javascript = tag.script('\n'.join(javascript), **{ "type": "text/javascript"})
            stream |= Transformer("head").append(javascript)

        return stream

    ### methods returning JS

    def onload(self, items):
        return """
function onload()
{
%s
}
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
function onsubmit()
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

"""
        return string

    ### methods for IAdminPanelProvider

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        return []

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        
    ### methods for ITemplateProvider

    def get_htdocs_dirs():
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """

    def get_templates_dirs():
        """Return a list of directories containing the provided template
        files.
        """
