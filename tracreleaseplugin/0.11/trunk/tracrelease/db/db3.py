# -*- coding: utf-8 -*-
# Copyright (C) 2008-2013 Joao Alexandre de Toledo <tracrelease@toledosp.com.br>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.db import DatabaseManager

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    cursor.execute("INSERT INTO install_procedures (id, name, description, contain_files) VALUES (1, 'Instalacao Padrao JBoss', 'Instalacao padrao no JBoss', 0)")
    cursor.execute("INSERT INTO install_procedures (id, name, description, contain_files) VALUES (2, 'Execucao de Scripts', 'Execucao de Scripts no Oracle', 1)")

    # Set database schema version.    
    cursor.execute("UPDATE system SET value = '3' WHERE name = 'release_version'")
