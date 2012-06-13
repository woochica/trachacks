# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac.core import *
from trac.util.text import to_unicode

def smp_settings(req, context, kind, name):
    
    if name:
        settings_name       = '%s-%s' % (kind, name)
        settings_settings   = '%s.%s.%s' % (context, kind, name)
    else:
        settings_name       = '%s' % kind
        settings_settings   = '%s.%s' % (context, kind)

    settings = req.args.get(settings_name)
    settings = type(settings) is unicode and (settings,) or settings

    # check session attribtes
    if not settings:
        if req.session.has_key(settings_settings):
            settings = to_unicode(req.session[settings_settings])
    else:
        req.session[settings_settings] = settings

    return settings

def smp_filter_settings(req, context, name):
    settings = smp_settings(req, context, 'filter', name)

    if settings and u'All' in settings:
        settings = None

    return settings


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

    # Ticket Methods
    def get_ticket_project(self, id):
        cursor = self.__get_cursor()
        query    = """SELECT
                        value
                      FROM
                        ticket_custom
                      WHERE
                        name = 'project' AND ticket = %i""" % id
        cursor.execute(query)
        self.__start_transacction()

        return cursor.fetchone()
        

    # MilestoneProject Methods
    def insert_milestone_project(self, milestone, id_project):
        cursor = self.__get_cursor()
        query = """INSERT INTO
                        smp_milestone_project(milestone, id_project)
                    VALUES ('%s', %s)""" % (milestone, str(id_project))
        cursor.execute(query)
        self.__start_transacction()

    def get_milestones_of_project(self,project):
        cursor = self.__get_cursor()
        query = """SELECT
                        m.milestone AS milestone
                   FROM
                        smp_project AS p,
                        smp_milestone_project AS m
                   WHERE
                        p.name = '%s' AND
                        p.id_project = m.id_project""" % (project)

        cursor.execute(query)
        return cursor.fetchall()

    def get_milestones_for_projectid(self,projectid):
        cursor = self.__get_cursor()
        query = """SELECT
                        milestone
                   FROM
                        smp_milestone_project
                   WHERE
                        id_project = %i""" % (projectid)

        cursor.execute(query)
        return cursor.fetchall()

        

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

    def rename_milestone_project(self,old_milestone,new_milestone):
        cursor = self.__get_cursor()
        query = '''UPDATE
                        smp_milestone_project
                   SET
                        milestone='%s' WHERE milestone='%s';''' % (new_milestone,old_milestone)

        cursor.execute(query)
        self.__start_transacction()

    # VersionProject Methods
    def insert_version_project(self, version, id_project):
        cursor = self.__get_cursor()
        query = """INSERT INTO
                        smp_version_project(version, id_project)
                    VALUES ('%s', %s)""" % (version, str(id_project))
        cursor.execute(query)
        self.__start_transacction()

    def get_versions_of_project(self,project):
        cursor = self.__get_cursor()
        query = """SELECT
                        m.version AS version
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        p.name = '%s' AND
                        p.id_project = m.id_project""" % (project)

        cursor.execute(query)
        return cursor.fetchall()

    def get_versions_for_projectid(self,projectid):
        cursor = self.__get_cursor()
        query = """SELECT
                        version
                   FROM
                        smp_version_project
                   WHERE
                        id_project = %i""" % (projectid)

        cursor.execute(query)
        return cursor.fetchall()

        

    def get_project_version(self,version):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        m.version='%s' and
                        m.id_project = p.id_project""" % (version)

        cursor.execute(query)
        return cursor.fetchone()

    def get_id_project_version(self,version):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_version_project
                   WHERE
                        version='%s';""" % (version)

        cursor.execute(query)
        return cursor.fetchone()

    def delete_version_project(self,version):
        cursor = self.__get_cursor()
        query = """DELETE FROM
                        smp_version_project
                   WHERE
                        version='%s';""" % (version)

        cursor.execute(query)
        self.__start_transacction()

    def update_version_project(self,version,project):
        cursor = self.__get_cursor()
        query = '''UPDATE
                        smp_version_project
                   SET
                        id_project='%s' WHERE version='%s';''' % (str(project),version)

        cursor.execute(query)
        self.__start_transacction()

    def get_id_project_version(self,version):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_version_project
                   WHERE
                        version='%s';""" % (version)

        cursor.execute(query)
        return cursor.fetchone()

    def rename_version_project(self,old_version,new_version):
        cursor = self.__get_cursor()
        query = '''UPDATE
                        smp_version_project
                   SET
                        version='%s' WHERE version='%s';''' % (new_version,old_version)

        cursor.execute(query)
        self.__start_transacction()
