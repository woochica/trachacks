from trac.db import Table, Column

name = 'tracforge.admin'
version = 6
tables = [
    Table('tracforge_projects', key='name')[
        Column('name'),
        Column('env_path'),
    ],
    Table('tracforge_project_log', key=('project', 'step'))[
        Column('project'),
        Column('step'),
        Column('args'),
        Column('return'),
    ],
    Table('tracforge_project_output', key='id')[
        Column('id', auto_increment=True),
        Column('project'),
        Column('step'),
        Column('line'),
        Column('stream'),
    ],
    Table('tracforge_members', key=('project', 'user'))[
        Column('project'),
        Column('user'),
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
