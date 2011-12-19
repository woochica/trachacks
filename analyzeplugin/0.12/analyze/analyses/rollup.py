# several rollup-related analyses and fixes
# TODO: fix sql injection strings

import copy

def get_solutions(db, args):
    """For each blockedby ticket of this id, check that it's queue
    position is <= this ticket's position.
    """
    solutions = []
    id = args['id1']
    
    # iterate over the fields in same order every time
    standard = [field for field in args['standard_fields'].keys()]
    custom = [field for field in args['custom_fields'].keys()]
    
    # queue fields are all good, so how's their order?
    old,tickets = _get_rollup_fields(db, args, standard, custom, id)
    if not old or not tickets:
        return '',[] # no rollup tickets!  skip
    
    changes = []
    new = {'ticket':id}
    for field in standard + custom:
        if field in args['standard_fields']:
            rollup = args['standard_fields'][field]
        else:
            rollup = args['custom_fields'][field]
        
        # compare old and new values
        old_value = _get_value(old[field], rollup)
        new_value = _get_stat_rollup(field, rollup, tickets)
        if old_value != new_value:
            new[field] = str(new_value)
            if new_value == '':
                new_value = '(empty)'
            changes.append("%s to %s" % (field,new_value))
    if len(new) == 1:
        return '',[] # no changes
    
    # solution 1: update rollup field changes
    issue = "#%s has rollup field changes." % id
    solutions.append({
      'name': 'Update %s' % (', '.join(changes)),
      'data': new,
    })
    return issue,solutions


# common functions

def _get_value(value, rollup):
    if not value:
        return value
    if rollup['numeric']:
        try:
            return int(value)
        except (ValueError, TypeError):
            return float(value)
    return value

def _get_stat_rollup(field, rollup, tickets):
    options = rollup['options']
    if rollup['numeric']:
        vals = [_get_value(ticket[field], rollup) for ticket in tickets \
                if ticket[field]] # guard against empty data
    else:
        vals = [options.index(ticket[field]) for ticket in tickets \
                if ticket[field] in options] # guard against bad data
    
    if rollup['stat'] == 'sum':
        return sum(vals)
    if rollup['stat'] == 'min':
        if rollup['numeric']:
            return min(vals)
        else:
            return options[min(vals)]
    if rollup['stat'] == 'max':
        if rollup['numeric']:
            return max(vals)
        else:
            return options[max(vals)]
    if rollup['stat'] in ('avg','mean'):
        avg = sum(vals)/len(vals)
        if rollup['numeric']:
            return avg # TODO: handle precision of floats
        else:
            return options[avg]
    if rollup['stat'] == 'median':
        vals.sort()
        mid = len(vals)/2
        if rollup['numeric']:
            return vals[mid]
        else:
            return options[vals[mid]]
    if rollup['stat'] == 'mode':
        vals.sort()
        counts = {}
        hi_count = 0
        hi_value = 0
        for val in vals:
            counts[val] = counts.get(val,0)+1
            if counts[val] > hi_count:
                hi_count = counts[val]
                hi_val = val
        if rollup['numeric']:
            return hi_val
        else:
            return options[hi_val]
    
    # assume stat is the pivot field - the pivot algorithm is as follows:
    # 
    #  * if all values are < the pivot index, then select their max index
    #  * else if all are > the pivot index, then select their min index
    #  * else select the pivot index
    index = options.index(rollup['stat'])
    max_index = max(vals)
    if max_index < index:
        return options[max_index]
    min_index = min(vals)
    if min_index > index:
        return options[min_index]
    return options[index]

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

def _get_rollup_fields(db, args, standard, custom, id):
    """Return ticket id's rollup fields and all of its children tickets
    recursively."""
    cursor = db.cursor()
    project_type = args['project_type']
    
    # build field selectors
    keys = standard + custom
    fields = ["t."+name for name in standard]
    fields += ["c%d.value" % i for i in range(len(custom))]
    
    # build "from" part of query
    from_  = " FROM ticket t"
    from_ += _get_join(custom)
        
    # get this ticket's rollup field values 
    sql = "SELECT " + ', '.join(fields) + from_ + "WHERE t.id = %s" % id
    cursor.execute(sql)
    result = cursor.fetchone()
    if not result:
        return {},[]
    ticket = {'ticket':id}
    for i in range(len(keys)):
        name = keys[i]
        ticket[name] = result[i]
    
    sql = "SELECT t.id, " + ', '.join(fields) + from_ + "WHERE t.id IN"
    sql += " (SELECT source FROM mastertickets WHERE dest = %s)" # % id
    sql += " AND t.status != 'closed' AND t.type != '%s'" % project_type
    sql += " AND t.id NOT IN (%s);" # skip visited tickets
    visited = [id]
    recurse = args['recurse']
    tickets = _get_rollup_children(cursor, sql, id, keys, visited, recurse)
    return ticket,tickets


def _get_rollup_children(cursor, sql, id, keys, visited, recurse):
    """Recursively return all children tickets of the given id that have
    not yet been visited."""
    # find open dependent tickets that haven't been seen yet
    tickets = []
    cursor.execute(sql % (id,','.join(visited)))
    for result in cursor:
        cid = str(result[0])
        visited.append(cid) # add ticket id to visited
        ticket = {'id':cid}
        for i in range(len(keys)):
            name = keys[i]
            ticket[name] = result[i+1]
        tickets.append(ticket)
    
    # now get children tickets (separate loop to avoid confusing cursor)
    children = []
    if recurse:
        for ticket in tickets:
            id = ticket['id']
            children += _get_rollup_children(cursor,sql,id,keys,visited,recurse)
    
    return tickets + children
