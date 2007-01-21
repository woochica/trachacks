from trac.core import TracError
from trac.env import Environment
from trac.web.main import _open_environment
from trac.wiki.model import WikiPage
from trac.ticket.model import Component as TicketComponent, Milestone, Version
from trac.attachment import Attachment

from shutil import copyfile
import os
__all__ = ['copy_ticket', 'copy_wiki_page', 'copy_component', 'copy_enum', 'copy_milestone', 'copy_attachment', 'copy_version']


def make_query(data, table):
    sql = 'INSERT INTO ' + table + ' ' + \
          '(' + ', '.join(data.keys()) + ') ' + \
          'VALUES (' + ', '.join(['%s']*len(data)) + ')'
    return (sql, data.values())
    


def copy_ticket(source_env, dest_env, source_id, dest_db=None):
    """Copy a ticket from {{{source_env}}} #{{{source_id}}} to {{{dest_env}}}."""
    
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
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
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving page %s to the environment at %s', name, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving page %s from the environment at %s', name, source_env.path)
        
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

def copy_component(source_env, dest_env, name, dest_db=None):
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving component %s to the environment at %s', name, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving component %s from the environment at %s', name, source_env.path)
    
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    # Remove the component from the destination
    try:
        dest_comp = TicketComponent(dest_env, name, db=dest_db)
        dest_comp.delete(db=dest_db)
    except TracError:
        pass

    # Copy each entry in the component table
    source_cursor.execute('SELECT * FROM component WHERE name=%s',(name,))
    for row in source_cursor:
        comp_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(comp_data, 'component')
        dest_cursor.execute(*q)
       
    if handle_commit:
        dest_db.commit()

def copy_enum(source_env, dest_env, etype, name, dest_db=None):
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving enum (%s,%s) to the environment at %s', etype, name, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving enum (%s,%s) from the environment at %s', etype, name, source_env.path)
    
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    # Remove the enum from the destination
    dest_cursor.execute('DELETE FROM enum WHERE type=%s AND name=%s', (etype, name))

    # Copy each entry in the component table
    source_cursor.execute('SELECT * FROM enum WHERE type=%s AND name=%s',(etype,name))
    for row in source_cursor:
        enum_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(enum_data, 'enum')
        dest_cursor.execute(*q)
       
    if handle_commit:
        dest_db.commit()

def copy_milestone(source_env, dest_env, name, dest_db=None):
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving milestone %s to the environment at %s', name, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving milestone %s from the environment at %s', name, source_env.path)
    
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    # Remove the milestone from the destination
    try:
        dest_milestone = Milestone(dest_env, name, db=dest_db)
        dest_milestone.delete(retarget_to=name, db=dest_db)
    except TracError:
        pass

    # Copy each entry in the milestone table
    source_cursor.execute('SELECT * FROM milestone WHERE name=%s',(name,))
    for row in source_cursor:
        milestone_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(milestone_data, 'milestone')
        dest_cursor.execute(*q)
       
    if handle_commit:
        dest_db.commit()

def copy_attachment(source_env, dest_env, parent_type, parent_id, filename, dest_db=None):
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving attachment (%s,%s,%s) to the environment at %s', parent_type, parent_id, filename, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving attachment (%s,%s,%s) from the environment at %s', parent_type, parent_id, filename, source_env.path)
    
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    # Remove the attachment from the destination
    try:
        dest_attachment = Attachment(dest_env, parent_type, parent_id, filename, db=dest_db)
        dest_attachment.delete(db=dest_db)
    except TracError:
        pass

    # Copy each entry in the attachments table
    source_cursor.execute('SELECT * FROM attachment WHERE type=%s AND id=%s AND filename=%s',(parent_type, parent_id, filename))
    for row in source_cursor:
        att_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(att_data, 'attachment')
        dest_cursor.execute(*q)
        # now copy the file itself
        old_att = Attachment(source_env, parent_type, parent_id, filename, db=source_db)
        new_att = Attachment(dest_env, parent_type, parent_id, filename, db=dest_db)
        if not os.path.isdir(os.path.dirname(new_att.path)):
            os.makedirs(os.path.dirname(new_att.path))
        copyfile(old_att.path, new_att.path)
       
    if handle_commit:
        dest_db.commit()

def copy_version(source_env, dest_env, name, dest_db=None):
    # In case a string gets passed in
    if not isinstance(source_env, Environment):
        source_env = _open_environment(source_env)
    if not isinstance(dest_env, Environment):
        dest_env = _open_environment(dest_env)
        
    # Log message
    source_env.log.info('DatamoverPlugin: Moving version %s to the environment at %s', name, dest_env.path)
    dest_env.log.info('DatamoverPlugin: Moving version %s from the environment at %s', name, source_env.path)
    
    # Open databases
    source_db = source_env.get_db_cnx()
    source_cursor = source_db.cursor()
    handle_commit = True
    if not dest_db:
        dest_db, handle_commit = dest_env.get_db_cnx(), False
    dest_cursor = dest_db.cursor()
    
    # Remove the version from the destination
    try:
        dest_version = Version(dest_env, name, db=dest_db)
        dest_version.delete(db=dest_db)
    except TracError:
        pass

    # Copy each entry in the version table
    source_cursor.execute('SELECT * FROM version WHERE name=%s',(name,))
    for row in source_cursor:
        version_data = dict(zip([d[0] for d in source_cursor.description], row))
        q = make_query(version_data, 'version')
        dest_cursor.execute(*q)
       
    if handle_commit:
        dest_db.commit()
