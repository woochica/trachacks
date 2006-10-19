from trac.db import Table, Column

version = 3
tables = [
    Table('tracforge_projects', key='name')[
        Column('name'),
        Column('env_path'),
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
    Table('tracforge_prototypes', key='step')[
        Column('step', auto_increment=True),
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
