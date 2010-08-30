# -*- coding: utf-8 -*-
#! /usr/bin/env python
#
# This python script removes the Google Map Macro cache table
# from the Trac DataBase. Please set your Trac directory below!
#
from trac.env import Environment

tracdir = "<YOUR TRAC DIRECTORY>"
env = Environment(tracdir)
db  = env.get_db_cnx()
cursor = db.cursor()

cursor.execute("DROP TABLE 'googlemapmacro';")
db.commit()

