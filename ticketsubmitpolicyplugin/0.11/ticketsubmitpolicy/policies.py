"""policies for ITicketSubmitPolicy"""

import simplejson

from genshi.filters import Transformer
from interface import ITicketSubmitPolicy
from trac.core import Component, implements

class TicketRequires(Component):
    """bits for requiring a field"""
    implements(ITicketSubmitPolicy)

    def name(self):
        return 'requires'

    def javascript(self):
        return 'ticketsubmitpolicy/js/requires.js'

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
        return 'ticketsubmitpolicy/js/exclude.js'

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
