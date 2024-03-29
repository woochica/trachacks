# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac import __version__ as VERSION
from trac.core import *
from trac.util.text import to_unicode

def smp_settings(req, context, kind, name=None):
    
    if name:
        settings_name       = '%s-%s' % (kind, name)
        settings_settings   = '%s.%s.%s' % (context, kind, name)
    else:
        settings_name       = '%s' % kind
        settings_settings   = '%s.%s' % (context, kind)

    settings = req.args.get(settings_name)
    if type(settings) is list:
        new_settings = u''
        for setting in settings:
            new_settings = "%s,///,%s" % (setting,new_settings)

        settings = new_settings

    # check session attribtes
    if not settings:
        if req.session.has_key(settings_settings):
            settings = req.session[settings_settings]
    else:
        req.session[settings_settings] = settings

    if settings is None:
        return None
    else:
        return settings.split(",///,")

def smp_filter_settings(req, context, name):
    settings = smp_settings(req, context, 'filter', name)

    if settings and u'All' in settings:
        settings = None

    return settings


class SmpModel(Component):

    # DB Method
    def __get_cursor(self):
        if VERSION < '0.12':
            self.db = self.env.get_db_cnx()
        else:
            self.db = self.env.get_read_db()
        return self.db.cursor()
    
    def __start_transacction(self):
        if VERSION < '0.12':
            # deprecated in newer versions
            self.db.commit()
            self.db.close()

    # Commons Methods
    def get_project_info(self, name):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project,name,summary,description
                   FROM
                        smp_project
                   WHERE
                        name = %s"""
        
        cursor.execute(query, [name])
        return  cursor.fetchone()
        
    def get_all_projects(self):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project,name,summary,description
                   FROM
                        smp_project"""
        
        cursor.execute(query)
        return  cursor.fetchall()

    def get_project_name(self, project_id):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project
                   WHERE
                        id_project=%s"""
        
        cursor.execute(query, [str(project_id)])
        result = cursor.fetchone()

        if result:
            name = result[0]
        else:
            name = None

        return name

    def update_custom_ticket_field(self, old_project_name, new_project_name):
        cursor = self.__get_cursor()

        query    = """UPDATE
                        ticket_custom
                      SET
                        value = %s
                      WHERE
                        name = 'project' AND value = %s"""

        cursor.execute(query, [new_project_name, old_project_name])

        self.__start_transacction()
        
    # AdminPanel Methods
    def insert_project(self, name, summary, description):
        cursor = self.__get_cursor()
        query    = """INSERT INTO
                        smp_project (name, summary, description)
                      VALUES (%s, %s, %s);"""

        cursor.execute(query, [name, summary, description])
        self.__start_transacction()

    def delete_project(self, ids_projects):
        cursor = self.__get_cursor()
        for id in ids_projects:
            query = """DELETE FROM smp_project WHERE id_project=%s"""
            cursor.execute(query, [id])
            
        self.__start_transacction()

    def update_project(self, id, name, summary, description):
        cursor = self.__get_cursor()

        query    = """UPDATE
                        smp_project
                      SET
                        name = %s, summary = %s, description = %s
                      WHERE
                        id_project = %s"""
        cursor.execute(query, [name, summary, description, id])

        self.__start_transacction()

    # Ticket Methods
    def get_ticket_project(self, id):
        cursor = self.__get_cursor()
        query    = """SELECT
                        value
                      FROM
                        ticket_custom
                      WHERE
                        name = 'project' AND ticket = %s"""
        cursor.execute(query, [id])
        self.__start_transacction()

        return cursor.fetchone()
        

    # MilestoneProject Methods
    def insert_milestone_project(self, milestone, id_project):
        cursor = self.__get_cursor()
        query = """INSERT INTO
                        smp_milestone_project(milestone, id_project)
                    VALUES (%s, %s)"""
        cursor.execute(query, [milestone, str(id_project)])
        self.__start_transacction()

    def get_milestones_of_project(self,project):
        cursor = self.__get_cursor()
        query = """SELECT
                        m.milestone AS milestone
                   FROM
                        smp_project AS p,
                        smp_milestone_project AS m
                   WHERE
                        p.name = %s AND
                        p.id_project = m.id_project"""

        cursor.execute(query, [project])
        return cursor.fetchall()

    def get_milestones_for_projectid(self,projectid):
        cursor = self.__get_cursor()
        query = """SELECT
                        milestone
                   FROM
                        smp_milestone_project
                   WHERE
                        id_project = %s"""

        cursor.execute(query, [projectid])
        return cursor.fetchall()

        

    def get_project_milestone(self,milestone):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_milestone_project AS m
                   WHERE
                        m.milestone=%s and
                        m.id_project = p.id_project"""

        cursor.execute(query, [milestone])
        return cursor.fetchone()

    def get_id_project_milestone(self,milestone):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_milestone_project
                   WHERE
                        milestone=%s;"""

        cursor.execute(query, [milestone])
        return cursor.fetchone()

    def delete_milestone_project(self, milestone):
        cursor = self.__get_cursor()
        query = """DELETE FROM
                        smp_milestone_project
                   WHERE
                        milestone=%s;"""

        cursor.execute(query, [milestone])
        self.__start_transacction()

    def update_milestone_project(self,milestone,project):
        cursor = self.__get_cursor()
        query = """UPDATE
                        smp_milestone_project
                   SET
                        id_project=%s WHERE milestone=%s;"""

        cursor.execute(query, [str(project), milestone])
        self.__start_transacction()

    def rename_milestone_project(self,old_milestone,new_milestone):
        cursor = self.__get_cursor()
        query = """UPDATE
                        smp_milestone_project
                   SET
                        milestone=%s WHERE milestone=%s;"""

        cursor.execute(query, [new_milestone, old_milestone])
        self.__start_transacction()

    # VersionProject Methods
    def insert_version_project(self, version, id_project):
        cursor = self.__get_cursor()
        query = """INSERT INTO
                        smp_version_project(version, id_project)
                    VALUES (%s, %s)"""
        cursor.execute(query, [version, str(id_project)])
        self.__start_transacction()

    def get_versions_of_project(self,project):
        cursor = self.__get_cursor()
        query = """SELECT
                        m.version AS version
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        p.name = %s AND
                        p.id_project = m.id_project"""

        cursor.execute(query, [project])
        return cursor.fetchall()

    def get_versions_for_projectid(self,projectid):
        cursor = self.__get_cursor()
        query = """SELECT
                        version
                   FROM
                        smp_version_project
                   WHERE
                        id_project = %s"""

        cursor.execute(query, [projectid])
        return cursor.fetchall()

        

    def get_project_version(self,version):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        m.version=%s and
                        m.id_project = p.id_project"""

        cursor.execute(query, [version])
        return cursor.fetchone()

    def get_id_project_version(self,version):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_version_project
                   WHERE
                        version=%s;"""

        cursor.execute(query, [version])
        return cursor.fetchone()

    def delete_version_project(self,version):
        cursor = self.__get_cursor()
        query = """DELETE FROM
                        smp_version_project
                   WHERE
                        version=%s;"""

        cursor.execute(query, [version])
        self.__start_transacction()

    def update_version_project(self,version,project):
        cursor = self.__get_cursor()
        query = """UPDATE
                        smp_version_project
                   SET
                        id_project=%s WHERE version=%s;"""

        cursor.execute(query, [str(project), version])
        self.__start_transacction()

    def rename_version_project(self,old_version,new_version):
        cursor = self.__get_cursor()
        query = """UPDATE
                        smp_version_project
                   SET
                        version=%s WHERE version=%s;"""

        cursor.execute(query, [new_version, old_version])
        self.__start_transacction()

    # ComponentProject Methods
    def insert_component_projects(self, component, id_projects):
        cursor = self.__get_cursor()
                 
        if type(id_projects) is not list:
            id_projects = [id_projects]

        for id_project in id_projects:
            query = """INSERT INTO smp_component_project(component, id_project) VALUES (%s, %s)"""
            cursor.execute(query, [component, id_project])
            
        self.__start_transacction()

    def get_components_of_project(self,project):
        cursor = self.__get_cursor()
        query = """SELECT
                        m.component AS component
                   FROM
                        smp_project AS p,
                        smp_component_project AS m
                   WHERE
                        p.name = %s AND
                        p.id_project = m.id_project"""

        cursor.execute(query, [project])
        return cursor.fetchall()

    def get_components_for_projectid(self,projectid):
        cursor = self.__get_cursor()
        query = """SELECT
                        component
                   FROM
                        smp_component_project
                   WHERE
                        id_project = %s"""

        cursor.execute(query, [projectid])
        return cursor.fetchall()

    def get_projects_component(self,component):
        cursor = self.__get_cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_component_project AS m
                   WHERE
                        m.component=%s and
                        m.id_project = p.id_project"""

        cursor.execute(query, [component])
        return cursor.fetchall()

    def get_id_projects_component(self,component):
        cursor = self.__get_cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_component_project
                   WHERE
                        component=%s;"""

        cursor.execute(query, [component])
        return cursor.fetchall()

    def delete_component_projects(self,component):
        cursor = self.__get_cursor()
        query = """DELETE FROM
                        smp_component_project
                   WHERE
                        component=%s;"""

        cursor.execute(query, [component])
        self.__start_transacction()

    def rename_component_project(self,old_component,new_component):
        cursor = self.__get_cursor()
        query = """UPDATE
                        smp_component_project
                   SET
                        component=%s WHERE component=%s;"""

        cursor.execute(query, [new_component, old_component])
        self.__start_transacction()
