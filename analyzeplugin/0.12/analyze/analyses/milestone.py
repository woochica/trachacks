# several milestone-related analyses

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
        return '',[]
    type,milestone,due = result
    if not due:
        return '',[] # this ticket's milestone doesn't have a due date - skip 
    
    # find all peers that are due too late (or not scheduled at all)
    cursor.execute("""
        SELECT t.id, t.milestone, m.due FROM ticket t
        JOIN milestone m ON t.milestone = m.name
        WHERE t.id IN (SELECT source FROM mastertickets WHERE dest = %s)
        AND t.status != 'closed'
        AND (t.milestone='' OR m.due=0 OR m.due > %s);
        """, (id,due))
    result = zip(*[(t,m,d) for t,m,d in cursor])
    if not result:
        return '',[] # no dependent tickets!  skip
    
    issue = "#%s's dependent tickets are in future (or no) milestones." % id
    ids,milestones,dues = result
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
    if any(m for m in milestones) and any(d for d in dues):
        cursor.execute("""
            SELECT name FROM milestone WHERE due =
              (SELECT max(due) FROM milestone WHERE name in (%s));
            """ % ','.join(["'%s'" % m for m in milestones if m]))
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
    
    return issue,solutions
