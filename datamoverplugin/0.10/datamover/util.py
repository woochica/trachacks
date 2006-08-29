from trac.env import Environment
from trac.wiki.model import WikiPage

__all__ = ['copy_ticket', 'copy_wiki_page']


def make_query(data, table):
    sql = 'INSERT INTO ' + table + ' ' + \
          '(' + ', '.join(data.keys()) + ') ' + \
          'VALUES (' + ', '.join(['%s']*len(data)) + ')'
    return (sql, data.values())
    


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

def copy_wiki_page(source_env, dest_env, name, dest_db=None):
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
    
    # Remove the page from the destination
    dest_page = WikiPage(dest_env, name, db=dest_db)
    if dest_page.exists:
        dest_page.delete(db=dest_db)

    # Copy each entry in the wiki table
    source_cursor.execute('SELECT * FROM wiki WHERE name=%s',(name,))
    for row in source_cursor:
        wiki_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(wiki_data, 'wiki')
        dest_cursor.execute(*q)
       
    if handle_commit:
        dest_db.commit()
