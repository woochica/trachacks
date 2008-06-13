"""policies for ITicketSubmitPolicy"""

from genshi.filters import Transformer
from interface import ITicketSubmitPolicy
from trac.core import *

class TicketRequires(Component):
    """bits for requiring a field"""
    implements(ITicketSubmitPolicy)

    def name(self):
        return 'requires'

    def javascript(self):
        return """
function requires(policy, requiredfields)
{

var missing = new Array();

if (condition(policy))
{

for ( var i=0; i != requiredfields.length; i++ )
{

var field=getValue("field-" + requiredfields[i]);

if (!field)
{
missing.push(requiredfields[i]);
}

}

if (missing.length != 0)
{

if (missing.length == 1)
{
prestring = missing[0] + " is a required field ";
poststring = "Please provide this value.";
}
else
{
prestring = missing.join(", ") + " are required fields ";
poststring = "Please provide these values.";
}

return prestring + "for tickets where " + policytostring(policy) + ".\\n" + poststring;
}

}

return true;
}
""" 

    def onload(self, policy, condition, *args):
        return

    def onsubmit(self, policy, condition, *requiredfields):
        fields = repr([ str(i) for i in requiredfields ])
        requires = "requires(%s, %s);" % (policy, fields)
        return requires

    def filter_stream(self, stream, policy, condition, *args):
        return stream



### 

class TicketExcludes(Component):
    """bits for exluding field under a condition"""
    implements(ITicketSubmitPolicy)

    def name(self):
        return 'excludes'

    def javascript(self):
        return """function exclude(policy, excludedfields)
{

if (condition(policy))
{
display="none";
}
else
{
display="";
}

for (var i=0; i != excludedfields.length; i++)
{
excludedfield = excludedfields[i];
var element=document.getElementById("field-" + excludedfield);
element.style.display=display;
}

}

function excludeSubmit(policy, excludedfields)
{
var element=document.getElementById("field-" + excludedfield);
if (condition(policy))
{
element.value = "";
}
return true;
}

"""

    def onload(self, policy, condition, *excludedfields):
        fields = repr([ str(i) for i in excludedfields ])
        return "exclude(%s, %s);" % (policy, fields )

    def onsubmit(self, policy, condition, *excludedfields):
        fields = repr([ str(i) for i in excludedfields ])
        excludesubmit = "excludeSubmit(%s, %s);" % (policy, fields)
        return excludesubmit

    def filter_stream(self, stream, policy, condition, *excludedfields):
        fields = repr([ str(i) for i in excludedfields ])
        exclude = "exclude(%s, %s)" % ( policy, fields )

        # XXX this is unsafe, in the case onchange is already specified on this field;
        # see http://trac-hacks.org/ticket/3128
        for c in condition:
            field = c['field']
            stream |= Transformer("//select[@id='field-%s']" % field).attr('onchange', exclude)

        return stream
