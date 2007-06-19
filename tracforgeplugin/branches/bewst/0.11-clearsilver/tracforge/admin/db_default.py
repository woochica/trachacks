from trac.db import Table, Column

name = 'tracforge.admin'
version = 7
tables = [
    Table('tracforge_projects', key='name')[
        Column('name'),
        Column('env_path'),
    ],
    Table('tracforge_project_log', key=('project', 'action'))[
        Column('id', auto_increment=True),
        Column('project'),
        Column('action'),
        Column('args'),
        Column('return'),
        Column('stdout'),
        Column('stderr'),
    ],
    #Table('tracforge_project_output', key=('ts'
    Table('tracforge_members', key=('project', 'sid'))[
        Column('project'),
        Column('sid'),
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
