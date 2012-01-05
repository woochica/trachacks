# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac.core import *

class SmpModel(Component):

    # DB Method
    def __get_cursor(self):
        self.db = self.env.get_read_db()
        return self.db.cursor()
    
    def __start_transacction(self):
        self.db.commit()
        self.db.close()

    # Commons Methods
    def get_all_projects(self):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project,name,description
                   FROM
                        smp_project"""
        
        cursor.execute(query)
        return  cursor.fetchall()

    # AdminPanel Methods
    def insert_project(self, name, description):
        cursor = self.__get_cursor()
        query    = """INSERT INTO
                        smp_project (name, description)
                      VALUES ('%s', '%s');""" % (name, description)

        cursor.execute(query)
        self.__start_transacction()

    def delete_project(self, ids_projects):
        cursor = self.__get_cursor()
        for id in ids_projects:
            query = "DELETE FROM smp_project WHERE id_project='%s'" % id
            cursor.execute(query)
            
        self.__start_transacction()

    def update_project(self, id, name, description):
        cursor = self.__get_cursor()
        query    = """UPDATE
                        smp_project
                      SET
                        name = '%s', description = '%s'
                      WHERE
                        id_project = '%s'""" % (name, description, id)
        cursor.execute(query)
        self.__start_transacction()

    # MilestoneProject Methods
    def insert_milestone_project(self, milestone, id_project):
        cursor = self.__get_cursor()
        query = """INSERT INTO
                        smp_milestone_project(milestone, id_project)
                    VALUES ('%s', %s)""" % (milestone, str(id_project))
        cursor.execute(query)
        self.__start_transacction()

    def get_project_milestone(self,milestone):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_milestone_project AS m
                   WHERE
                        m.milestone='%s' and
                        m.id_project = p.id_project""" % (milestone)

        cursor.execute(query)
        return cursor.fetchone()

    def get_id_project_milestone(self,milestone):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_milestone_project
                   WHERE
                        milestone='%s';""" % (milestone)

        cursor.execute(query)
        return cursor.fetchone()

    def delete_milestone_project(self,milestone):
        cursor = self.__get_cursor()
        query = """DELETE FROM
                        smp_milestone_project
                   WHERE
                        milestone='%s';""" % (milestone)

        cursor.execute(query)
        self.__start_transacction()

    def update_milestone_project(self,milestone,project):
        cursor = self.__get_cursor()
        query = '''UPDATE
                        smp_milestone_project
                   SET
                        id_project='%s' WHERE milestone='%s';''' % (str(project),milestone)

        cursor.execute(query)
        self.__start_transacction()