from trac.env import Environment

__all__ = ['copy_ticket']

def copy_ticket(source_env, dest_env, source_id, dest_db=None):
    """Copy a ticket from {{{source_env}}} #{{{source_id}}} to {{{dest_env}}}."""
    
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = Environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = Environment(dest_env)
        
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    def make_query(data, table):
        sql = 'INSERT INTO ' + table + ' ' + \
              '(' + ', '.join(data.keys()) + ') ' + \
              'VALUES (' + ', '.join(['%s']*len(data)) + ')'
        return (sql, data.values())
    
    # Copy the 'ticket' table entry
    source_cursor.execute('SELECT * FROM ticket WHERE id=%s',(source_id,))
    ticket_data = dict(zip([d[0] for d in source_cursor.description], source_cursor.fetchone()))
    del ticket_data['id']
    q = make_query(ticket_data, 'ticket')
    dest_cursor.execute(*q)
    dest_id = dest_db.get_last_id(dest_cursor, 'ticket')
    
    # Copy the 'ticket_changes' entries
    source_cursor.execute('SELECT * FROM ticket_change WHERE ticket=%s',(source_id,))
    for row in source_cursor:
        ticket_change_data = dict(zip([d[0] for d in source_cursor.description], row))
        ticket_change_data['ticket'] = dest_id
        q = make_query(ticket_change_data, 'ticket_change')
        dest_cursor.execute(*q)
        
    # Copy the 'ticket_custom' entries
    source_cursor.execute('SELECT * FROM ticket_custom WHERE ticket=%s', (source_id,))
    for row in source_cursor:
        ticket_custom_data = dict(zip([d[0] for d in source_cursor.description], row))
        ticket_change_data['ticket'] = dest_id
        q = make_query(ticket_change_data, 'ticket_custom')
        dest_cursor.execute(*q)
    
    if handle_commit:
        dest_db.commit()

#t1 = '/var/www/coderanger/tracs/test1'
#t2 = '/var/www/coderanger/tracs/test2'
