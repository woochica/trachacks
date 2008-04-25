from trac.db import Table, Column

name = 'tracforge.admin'
version = 13
tables = [
    Table('tracforge_projects', key='name')[
        Column('name'),
        Column('env_path'),
        Column('status'),
    ],
    Table('tracforge_project_log', key=('project', 'direction', 'action', 'step_direction'))[
        Column('project'),
        Column('step', type='integer'),
        Column('direction'),
        Column('action'),
        Column('step_direction'),
        Column('args'),
        Column('return'),
        Column('undone', type='integer'),
    ],
    Table('tracforge_project_output', key=('ts', 'project', 'direction',
                                           'action', 'step_direction', 'stream'))[
        Column('ts'),
        Column('project'),
        Column('direction'),
        Column('action'),
        Column('stream'),
        Column('step_direction'),
        Column('data'),
    ],
    Table('tracforge_members', key=('project', 'username'))[
        Column('project'),
        Column('username'),
        Column('role'),
    ],
    Table('tracforge_permission', key=('username', 'action'))[
        Column('username'),
        Column('action'),
    ],
    Table('tracforge_prototypes', key=('tag', 'step'))[
        Column('tag'),
        Column('step', type='integer'),
        Column('action'),
        Column('args'),
    ],
    Table('tracforge_configs', key=('tag', 'section', 'key'))[
        Column('tag'),
        Column('section'),
        Column('key'),
        Column('value'),
        Column('action'),
    ],
]

def rename_user_to_username(data):
    """Change tracforge_members.user to tracforge_members.username to work with
    Postgres as "user" is a keyword.
    """
    colnames = data['tracforge_members'][0]
    for i, col in enumerate(colnames):
        if col == 'user':
            colnames[i] = 'username'
    
migrations = [
    (xrange(1,8), rename_user_to_username),
]
