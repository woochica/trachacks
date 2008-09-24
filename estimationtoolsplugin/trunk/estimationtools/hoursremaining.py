from estimationtools.utils import get_estimation_field
from trac.core import TracError
from trac.wiki.macros import WikiMacroBase

class HoursRemaining(WikiMacroBase):
    """Calculates remaining estimated hours for given milestone.

    `milestone` is a mandatory parameter.
    
    Example:
    {{{
        [[HoursRemaining(milestone=Sprint 1)]]
    }}}
    """
        
    estimation_field = get_estimation_field()
    
    def render_macro(self, req, name, content):
        # you need 'TICKT_VIEW' or 'TICKET_VIEW_CC' (see PrivateTicketPatch) permissions
        if not (req.perm.has_permission('TICKET_VIEW') or 
                req.perm.has_permission('TICKET_VIEW_CC')):
            raise TracError('TICKET_VIEW or TICKET_VIEW_CC permission required')
        options = {}
        if content:
            for arg in content.split(','):
                i = arg.index('=')
                options[arg[:i].strip()] = arg[i+1:].strip()
        milestone = options.get('milestone')
        if not milestone:
            raise TracError("No milestone specified!")
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT p.value as estimation"
                       "  FROM ticket t, ticket_custom p"
                       "  WHERE p.ticket = t.id and p.name = %s"
                       "  AND t.milestone = %s", [self.estimation_field, milestone])
        
        sum = 0.0
        for estimation, in cursor:
            try:
                sum += float(estimation)
            except:
                pass

        return "%s" % int(sum)
        
