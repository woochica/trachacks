"""Several milestone-related analyses."""

def get_dependency_solutions(db, args):
    """For each blockedby ticket of this id, check that it's milestone's
    due date is <= this ticket's milestone's due date.
    """
    id = args['id1']
    cursor = db.cursor()
    
    # get the type and due date
    cursor.execute("""
        SELECT t.type, t.milestone, m.due
        FROM ticket t
        JOIN milestone m ON t.milestone = m.name
        WHERE t.id = %s;
        """, (id,))
    result = cursor.fetchone()
    if not result:
        return []
    type,milestone,due = result
    if not due:
        return []
    
    # find all peers that are due too late
    cursor.execute("""
        SELECT t.id, t.milestone FROM ticket t
        JOIN milestone m ON t.milestone = m.name
        WHERE t.id IN (SELECT source FROM mastertickets WHERE dest = %s)
        AND t.status != 'closed'
        AND m.due > %s;
        """, (id,due))
    result = zip(*[(t,m) for t,m in cursor])
    if not result:
        return []
    ids,milestones = result
    solutions = []
    
    # solution 1: move dependent tickets to this milestone
    tix = ', '.join(["#%s" % tid for tid in ids])
    data = []
    for tid in ids:
        changes = {'ticket':tid,'milestone':milestone}
        for field in args['on_change_clear']:
            changes.update({field:''})
        data.append(changes)
    solutions.append({
      'name': 'Move %s up to milestone %s' % (tix,milestone),
      'data': data,
    })
    
    # solution 2: move this ticket to latest dependent milestone
    cursor.execute("""
        SELECT name FROM milestone WHERE due =
          (SELECT max(due) FROM milestone WHERE name in (%s));
        """ % ','.join(["'%s'" % m for m in milestones]))
    result = cursor.fetchone()
    if result:
        (latest_milestone,) = result
        changes = {'ticket':id,'milestone':latest_milestone}
        for field in args['on_change_clear']:
            changes.update({field:''})
        solutions.append({
          'name': 'Move #%s out to milestone %s' % (id,latest_milestone),
          'data': changes,
        })
    
    return solutions
