# -*- coding: utf-8 -*-

from trac.core import *
from trac.db_default import Table, Column, Index

# Database version.
version = 1

# Database schema for version 1.
schema = [
  Table('guestbook', key='id')[
    Column('id', type='int', auto_increment = True),
    Column('author'),
    Column('time', type='int'),
    Column('title'),
    Column('body')]]
