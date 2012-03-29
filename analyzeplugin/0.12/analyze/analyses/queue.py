# several queue-related analyses and fixes
# TODO: fix sql injection strings

import copy

def get_dependency_solutions(db, args):
    """For each blockedby ticket of this id, check that it's queue
    position is <= this ticket's position.
    """
    solutions = []
    id = args['id1']
    position_field = args['col1_field1']
    position = int(args['col1_value1'])
    
    # iterate over the fields in same order every time
    standard = [field for field in args['standard_fields'].keys()]
    custom = [field for field in args['custom_fields'].keys()]
    
    # first check that the dependent ticket query fields are correct
    if standard or custom:
        issue = "#%s's dependent tickets are not in the correct queue." % id
        ticket,ids = _get_query_field_violators(db, args, standard, custom, id)
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
            return issue,solutions
    
    # queue fields are all good, so how's their order?
    issue = "#%s's dependent tickets are out of order." % id
    
    sql  = "SELECT t.id, c.value FROM ticket t"
    sql += " JOIN ticket_custom c ON t.id = c.ticket"
    sql += " AND c.name = '%s' " % position_field
    sql += _get_join(custom)
    sql += "WHERE t.id IN "
    sql += " (SELECT source FROM mastertickets WHERE dest = %s)" % id
    sql += " AND t.status != 'closed'"
    sql += _get_filter_and(standard, custom, args)
    sql += " AND (c.value = '' OR CAST(c.value AS INTEGER) > %s)" % position
    cursor = db.cursor()
    cursor.execute(sql)
    result = [(tid,pos) for tid,pos in cursor]
    if not result:
        return '',[] # no dependent tickets!  skip
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
        
    return issue,solutions


def get_project_solutions(db, args):
    """For each blockedby ticket of two ids, check that the first id's
    queue positions are <= all of the second id's queue positions.
    """
    solutions = []
    id1 = args['id1']
    id2 = args['id2']
    position_field = args['col1_field1']
    project_type = args['project_type']
    
    # iterate over the fields in same order every time
    standard = [field for field in args['standard_fields'].keys()]
    custom = [field for field in args['custom_fields'].keys()]
    
    # first check that the dependent ticket query fields are correct
    if standard or custom:
        for tid in (id1,id2):
            issue = "#%s's dependent tickets are not in the correct queue."%tid
            ticket,ids = _get_query_field_violators(db,args,standard,custom,tid)
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
                return issue,solutions
    
    # second do a multi-parent analysis - else can cause havoc!
    cursor = db.cursor()
    for tid in (id1,id2):
        # get all (unfiltered) children from this parent
        issue = "#%s's dependent tickets are in multiple %ss." % \
                    (tid,project_type)
        
        # for each child, determine if it has multiple parents
        sql  = "SELECT t.id, b.value FROM ticket t "
        sql += " JOIN ticket_custom b ON t.id=b.ticket AND b.name='blocking'"
        sql += _get_join(custom)
        sql += " WHERE t.id IN"
        sql += " (SELECT source FROM mastertickets WHERE dest=%s)" % tid
        sql += " AND t.status != 'closed'"
        sql += _get_filter_and(standard, custom, args) + ";"
        cursor.execute(sql)
        children = [(cid,[b.strip() for b in blocking.split(',')]) \
                    for (cid,blocking) in cursor]
        for cid,blocking in children:
            # for each child, determine if it has multiple parents
            sql  = "SELECT p.id FROM ticket p WHERE p.id IN"
            sql += " (SELECT dest FROM mastertickets WHERE source=%s)" % cid
            sql += "AND p.status != 'closed' "
            sql += "AND p.type = '%s';" % project_type
            cursor.execute(sql)
            ids = [pid for (pid,) in cursor]
            if len(ids) >= 2:
                for pid in ids:
                    rest = [str(i) for i in ids if i != pid]
                    block = [b for b in blocking if b not in rest]
                    tix = ', '.join(["#%s" % i for i in rest])
                    name = "%s%s" % (project_type,len(rest) > 1 and 's' or '')
                    solutions.append({
                      'name': 'Remove #%s from %s %s' % (cid,name,tix),
                      'data': {'ticket':cid,'blocking':', '.join(block)},
                    })
                return issue,solutions

    # queue fields are all good, so how's their childrens' order?
    issue = "#%s and #%s's dependent tickets are out of order." % (id1,id2)
    
    stats = [{'id':id1,'fn':'max','op':'>','label':'before'},
             {'id':id2,'fn':'min','op':'<','label':'after'}]
    for stat in stats:
        sql  = "SELECT %s(CAST(c.value AS INTEGER)) FROM ticket t" % stat['fn']
        sql += " JOIN ticket_custom c ON t.id = c.ticket"
        sql += " AND c.name = '%s' " % position_field
        sql += _get_join(custom)
        sql += "WHERE t.id IN "
        sql += " (SELECT source FROM mastertickets WHERE dest=%s)" % stat['id']
        sql += " AND t.status != 'closed'"
        sql += _get_filter_and(standard, custom, args) + ";"
        cursor.execute(sql)
        result = cursor.fetchone()
        stat['result'] = result and result[0] and int(result[0]) or -9999
        
    for i in range(len(stats)):
        stat = stats[i]
        j = (i+1)%2 # the other stat
        sql  = "SELECT t.id FROM ticket t"
        sql += " JOIN ticket_custom c ON t.id = c.ticket"
        sql += _get_join(custom)
        sql += " AND c.name = '%s' " % position_field
        sql += "WHERE t.id IN "
        sql += " (SELECT source FROM mastertickets WHERE dest=%s)" % stat['id']
        sql += " AND t.status != 'closed'"
        sql += _get_filter_and(standard, custom, args)
        sql += " AND (c.value = '' OR CAST(c.value AS INTEGER)"
        sql += "  %s %s)" % (stat['op'],stats[j]['result'])
        cursor = db.cursor()
        cursor.execute(sql)
        ids = [tid for (tid,) in cursor]
        pos = stats[j]['result']
        if ids and pos != -9999:
            # solution n: move project i's tickets before project j's
            #             highest/lowest position
            tix = ', '.join(["#%s" % tid for tid in ids])
            new_pos = str(pos + (i or -1)) # either -1 or +1
            solutions.append({
              'name': 'Move %s %s position %d' % (tix,stat['label'],pos),
              'data': [{'ticket':tid,position_field:new_pos} for tid in ids],
            })
    
    return issue,solutions


# common functions

def _is_filter_field(name, standard, custom, args):
    """Evaluates to True if the given name is a filter field."""
    return (name in standard and args['standard_fields'][name] or \
            name in custom and args['custom_fields'][name])
            
def _get_join(custom, t='t'):
    """Get JOIN sql query part for custom fields."""
    sql = ' '
    for i in range(len(custom)):
        name = custom[i]
        sql += "JOIN ticket_custom c%s ON %s.id = c%d.ticket " % (i,t,i)
        sql += "AND c%d.name = '%s' " % (i,name)
    return sql + ' '

def _get_filter_and(standard, custom, args):
    """Get AND sql query part for filtered standard and custom fields."""
    sql = ' '
    for name in standard:
        vals = copy.copy(args['standard_fields'][name])
        if not vals:
            continue
        not_ = vals.pop() and 'NOT IN' or 'IN'
        in_ = ','.join(["'%s'" % v for v in vals])
        sql += " AND t.%s %s (%s)" % (name,not_,in_)
    for i in range(len(custom)):
        name = custom[i]
        vals = copy.copy(args['custom_fields'][name])
        if not vals:
            continue
        not_ = vals.pop() and 'NOT IN' or 'IN'
        in_ = ','.join(["'%s'" % v for v in vals])
        sql += " AND c%d.value %s (%s)" % (i,not_,in_)
    return sql + ' '

def _get_query_field_violators(db, args, standard, custom, id):
    """Return ticket id's queue fields and any children tickets that do
    not have these fields (i.e., are in the wrong queue)."""
    cursor = db.cursor()
    
    # build field selectors
    keys = standard + custom
    fields = ["t."+name for name in standard]
    fields += ["c%d.value" % i for i in range(len(custom))]
    
    # build "from" part of query
    from_  = " FROM ticket t"
    from_ += " LEFT OUTER JOIN milestone m ON t.milestone = m.name "
    from_ += _get_join(custom)
        
    # get this ticket's queue field values 
    sql = "SELECT " + ', '.join(fields) + from_ + "WHERE t.id = %s" % id
    cursor.execute(sql)
    result = cursor.fetchone()
    if not result:
        return {},[]
    ticket = {}
    for i in range(len(keys)):
        name = keys[i]
        if (not _is_filter_field(name, standard, custom, args)):
            ticket[name] = result[i]
    
    # find open dependent tickets that don't match queue fields
    sql = "SELECT t.id " + from_
    sql += " WHERE t.id IN"
    sql += " (SELECT source FROM mastertickets WHERE dest = %s)" % id
    sql += " AND t.status != 'closed'"
    
    # add queue fields
    sql += " AND ("
    or_ = []
    for name in standard:
        if args['standard_fields'][name]:
            continue
        or_ += ["t.%s != '%s' " % (name,ticket[name])]
    for i in range(len(custom)):
        name = custom[i]
        if args['custom_fields'][name]:
            continue
        or_ += ["c%d.value != '%s' " % (i,ticket[name])]
    sql += ' OR '.join(or_) + ') '
    cursor.execute(sql)
    return ticket,[id for (id,) in cursor]
