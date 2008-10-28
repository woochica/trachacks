from trac.ticket.query import Query

def execute_query(env, req, query_string):
    query = Query.from_string(env, query_string)

    tickets = query.execute(req)

    tickets = [t for t in tickets 
               if ('TICKET_VIEW' or 'TICKET_VIEW_CC') in req.perm('ticket', t['id'])]
    
    return tickets

