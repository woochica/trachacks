"""Several queue-related analyses and fixes."""

def get_dependency_solutions(db, args):
    """For each blockedby ticket of this id, check that it's queue
    position is <= this ticket's position.
    """
    solutions = []
    id = args['id1']
    position_field = args['col1_field1']
    position = int(args['col1_value1'])
    
    # first check that the dependent ticket query fields are correct
    if args['standard_fields'] or args['custom_fields']:
        ticket,ids = _get_query_field_violators(db, args, id)
        if ids:
            data = []
            for tid in ids:
                changes = {'ticket':tid,position_field:str(position-1)}
                changes.update(ticket)
                data.append(changes)
            # solution 1: move dependent tickets to query fields and position-1
            tix = ', '.join(["#%s" % tid for tid in ids])
            fields = ', '.join(['%s %s' % (k,v) for k,v in ticket.items()])
            fields += ', and above position %d' % position
            solutions.append({
              'name': 'Move %s to %s' % (tix,fields),
              'data': data,
            })
            return solutions
    
    # queue fields are all good
    # so now check positions only
    sql  = "SELECT t.id, c.value FROM ticket t"
    sql += " JOIN ticket_custom c ON t.id = c.ticket"
    sql += " AND c.name = '%s' " % position_field
    sql += "WHERE t.id IN "
    sql += " (SELECT source FROM mastertickets WHERE dest = %s)" % id
    sql += " AND t.status != 'closed'"
    sql += " AND (c.value = '' OR CAST(c.value AS INTEGER) > %s)" % position
    cursor = db.cursor()
    cursor.execute(sql)
    result = [(tid,pos) for tid,pos in cursor]
    if not result:
        return []
    ids,positions = zip(*result)
    
    # solution 1: move dependent tickets above position
    tix = ', '.join(["#%s" % tid for tid in ids])
    solutions.append({
      'name': 'Move %s before position %d' % (tix,position),
      'data': [{'ticket':tid,position_field:str(position-1)} for tid in ids],
    })
    
    # solution 2: move this ticket below lowest position
    lowest = max([0] + [int(pos) for pos in positions if pos.strip()])
    if lowest: 
        solutions.append({
          'name': 'Move #%s after position %d' % (id,lowest),
          'data': {'ticket':id,position_field:str(lowest+1)},
        })
        
    return solutions

def get_project_solutions(db, args):
    """For each blockedby ticket of two ids, check that the first id's
    queue positions are <= all of the second id's queue positions.
    """
    solutions = []
    id1 = args['id1']
    id2 = args['id2']
    position_field = args['col1_field1']
    
    # first check that the dependent ticket query fields are correct
    if args['standard_fields'] or args['custom_fields']:
        for tid in (id1,id2):
            ticket,ids = _get_query_field_violators(db, args, tid)
            if ids:
                data = []
                for tid in ids:
                    changes = {'ticket':tid}
                    changes.update(ticket)
                    data.append(changes)
                # solution 1: move dependent tickets to query fields
                tix = ', '.join(["#%s" % tid for tid in ids])
                fields = ', '.join(['%s %s' % (k,v) for k,v in ticket.items()])
                solutions.append({
                  'name': 'Move %s to %s' % (tix,fields),
                  'data': data,
                })
                return solutions
    
    # queue fields are all good
    # so now check positions only of sub-tickets
    cursor = db.cursor()
    stats = [{'id':id1,'fn':'max','op':'>','label':'before'},
             {'id':id2,'fn':'min','op':'<','label':'after'}]
    for stat in stats:
        sql  = "SELECT %s(CAST(c.value AS INTEGER)) FROM ticket t" % stat['fn']
        sql += " JOIN ticket_custom c ON t.id = c.ticket"
        sql += " AND c.name = '%s' " % position_field
        sql += "WHERE t.id IN "
        sql += " (SELECT source FROM mastertickets WHERE dest=%s)" % stat['id']
        sql += " AND t.status != 'closed';"
        cursor.execute(sql)
        result = cursor.fetchone()
        stat['result'] = result and result[0] and int(result[0]) or 0
        
    for i in range(len(stats)):
        stat = stats[i]
        j = (i+1)%2 # the other stat
        sql  = "SELECT t.id FROM ticket t"
        sql += " JOIN ticket_custom c ON t.id = c.ticket"
        sql += " AND c.name = '%s' " % position_field
        sql += "WHERE t.id IN "
        sql += " (SELECT source FROM mastertickets WHERE dest=%s)" % stat['id']
        sql += " AND t.status != 'closed'"
        sql += " AND (c.value = '' OR CAST(c.value AS INTEGER)"
        sql += "  %s %s)" % (stat['op'],stats[j]['result'])
        cursor = db.cursor()
        cursor.execute(sql)
        ids = [tid for (tid,) in cursor]
        if ids:
            # solution n: move project i's tickets before project j's
            #             highest/lowest position
            tix = ', '.join(["#%s" % tid for tid in ids])
            pos = stats[j]['result']
            new_pos = str(pos + (i or -1)) # either -1 or +1
            solutions.append({
              'name': 'Move %s %s position %d' % (tix,stat['label'],pos),
              'data': [{'ticket':tid,position_field:new_pos} for tid in ids],
            })
    
    return solutions


def _get_query_field_violators(db, args, id):
    cursor = db.cursor()
    
    # build field selectors
    keys = [name for name in args['standard_fields']]
    keys += [name for name in args['custom_fields']]
    fields = ["t."+name for name in args['standard_fields']]
    fields += ["c%d.value" % i for i in range(len(args['custom_fields']))]
    
    # build "from" part of query
    from_  = " FROM ticket t "
    from_ += "LEFT OUTER JOIN milestone m ON t.milestone = m.name "
    for i in range(len(args['custom_fields'])):
        name = args['custom_fields'][i]
        from_ += "JOIN ticket_custom c%s ON t.id = c%d.ticket " % (i,i)
        from_ += "AND c%d.name = '%s' " % (i,name)
        
    # get this ticket's queue field values 
    sql = "SELECT m.due, " + ', '.join(fields) + from_ + "WHERE t.id = %s" % id
    cursor.execute(sql)
    result = cursor.fetchone()
    if not result:
        return []
    due = result[0] # for comparing milestone due date below
    ticket = {}
    for i in range(len(keys)):
        ticket[keys[i]] = result[i+1]
    
    # find open dependent tickets that don't match queue fields
    sql = "SELECT t.id " + from_ + "WHERE t.id IN"
    sql += " (SELECT source FROM mastertickets WHERE dest = %s)" % id
    sql += " AND t.status != 'closed' AND ("
    or_ = []
    for name in args['standard_fields']:
        if name == 'milestone': # special case: allow prior milestones
            or_ += ["t.milestone = '' OR m.due > %s " % (due or 0)]
        else:
            or_ += ["t.%s != '%s' " % (name,ticket[name])]
    for i in range(len(args['custom_fields'])):
        name = args['custom_fields'][i]
        or_ += ["c%d.value != '%s' " % (i,ticket[name])]
    sql += ' OR '.join(or_) + ') '
    cursor.execute(sql)
    return ticket,[id for (id,) in cursor]
