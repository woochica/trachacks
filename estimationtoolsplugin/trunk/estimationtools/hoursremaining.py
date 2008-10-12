from estimationtools.utils import get_estimation_field, execute_query
from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args

class HoursRemaining(WikiMacroBase):
    """Calculates remaining estimated hours for the queried tickets.

    The macro accepts a comma-separated list of query parameters for the ticket selection, 
    in the form "key=value" as specified in TracQuery#QueryLanguage.
    
    Example:
    {{{
        [[HoursRemaining(milestone=Sprint 1)]]
    }}}
    """
        
    estimation_field = get_estimation_field()
    
    def render_macro(self, req, name, content):
        _, options = parse_args(content, strict=False)

        # we have to add custom estimation field to query so that field is added to
        # resulting ticket list
        options[self.estimation_field + "!"] = None

        tickets = execute_query(self.env, req, options)
        
        sum = 0.0
        for t in tickets:
            try:
                sum += float(t[self.estimation_field])
            except:
                pass

        return "%s" % int(sum)
        
