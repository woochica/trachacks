# -*- coding: utf-8 -*-

import os
import shutil

from trac.core import Component, implements, TracError
from trac.admin.api import IAdminCommandProvider, get_dir_list
from trac.db.api import get_column_names
from trac.env import Environment
from trac.util.text import printout


class TracMigrationCommand(Component):

    implements(IAdminCommandProvider)

    def get_admin_commands(self):
        yield ('migrate', '<dir> <dburl>',
               'Migrate to new environment and another database',
               self._complete_migrate, self._do_migrate)

    def _do_migrate(self, env_path, dburl):
        options = [('trac', 'database', dburl)]
        options.extend((section, name, value)
                       for section in self.config.sections()
                       for name, value in self.config.options(section)
                       if section != 'trac' or name != 'database')
        src_db = self.env.get_read_db()
        src_cursor = src_db.cursor()
        src_tables = set(self._get_tables(self.config.get('trac', 'database'),
                                          src_cursor))
        env = Environment(env_path, create=True, options=options)
        env.upgrade()
        env.config.save() # remove comments

        db = env.get_read_db()
        cursor = db.cursor()
        tables = set(self._get_tables(dburl, cursor))
        tables = sorted(tables & src_tables)
        sequences = set(self._get_sequences(dburl, cursor, tables))
        directories = self._get_directories(src_db)

        printout('Copying tables:')
        for table in tables:
            if table == 'system':
                continue

            @env.with_transaction()
            def copy(db):
                cursor = db.cursor()
                printout('  %s table... ' % table, newline=False)
                src_cursor.execute('SELECT * FROM ' + src_db.quote(table))
                columns = get_column_names(src_cursor)
                query = 'INSERT INTO ' + db.quote(table) + \
                        ' (' + ','.join(db.quote(c) for c in columns) + ')' + \
                        ' VALUES (' + ','.join(['%s'] * len(columns)) + ')'
                cursor.execute('DELETE FROM ' + db.quote(table))
                count = 0
                while True:
                    rows = src_cursor.fetchmany(100)
                    if not rows:
                        break
                    cursor.executemany(query, rows)
                    count += len(rows)
                printout('%d records.' % count)

            if table in sequences:
                db.update_sequence(cursor, table)

        printout('Copying directories:')
        for name in directories:
            printout('  %s directory... ' % name, newline=False)
            src = os.path.join(self.env.path, name)
            dst = os.path.join(env.path, name)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            printout('done.')

    def _complete_migrate(self, args):
        if len(args) == 1:
            return get_dir_list(args[0])

    def _get_tables(self, dburl, cursor):
        if dburl.startswith('sqlite:'):
            query = "SELECT name FROM sqlite_master" \
                    " WHERE type='table' AND NOT name='sqlite_sequence'"
        elif dburl.startswith('postgres:'):
            query = "SELECT tablename FROM pg_tables" \
                    " WHERE schemaname = ANY (current_schemas(false))"
        elif dburl.startswith('mysql:'):
            query = "SHOW TABLES"
        else:
            raise TracError('Unsupported %s database' % dburl.split(':')[0])
        cursor.execute(query)
        return sorted([row[0] for row in cursor])

    def _get_sequences(self, dburl, cursor, tables):
        if dburl.startswith('postgres:'):
            tables = set(tables)
            cursor.execute(
                r"SELECT relname FROM pg_class "
                r"WHERE relkind='S' AND relname LIKE '%\_id\_seq'")
            seqs = [name[:-len('_id_seq')] for name, in cursor]
            return sorted(name for name in seqs if name in tables)
        return []

    def _get_directories(self, db):
        version = self.env.get_version(db=db)
        path = ('attachments', 'files')[version >= 28]
        return (path, 'htdocs', 'templates', 'plugins')
