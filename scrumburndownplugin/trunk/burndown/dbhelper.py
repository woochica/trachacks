from datetime import datetime
import time

from trac.db import Column, DatabaseManager, Index, Table

burndown_table = Table('burndown', key='id')[
    Column('id', auto_increment=True),
    Column('component_name'),
    Column('milestone_name'),
    Column('date'),
    Column('hours_remaining', type='int'),
    Index(['id'])]

milestone_table = Table('milestone', key='name')[Column('name'),
                                                 Column('due', type='int'),
                                                 Column('completed',
                                                        type='int'),
                                                 Column('description'),
                                                 Column('started', type='int')]


def get_current_milestone(db, milestone_name):
    cursor = db.cursor()
    mile = None

    if milestone_name is not None:
        mile = get_milestone(db, milestone_name)

    if not mile:
        cursor.execute(
            "select name from milestone order by started desc, name limit 1")
        milestone = cursor.fetchone()
        if milestone:
            mile = get_milestone(db, milestone[0])

    return mile


def empty_db_for_testing(db):
    cursor = db.cursor()
    cursor.execute("delete from ticket_custom")
    cursor.execute("delete from ticket")
    cursor.execute("delete from burndown")
    cursor.execute("update milestone set started=0, completed=0, due=0")
    cursor.execute("update milestone set due=%s where name='milestone1'",
                   [time.time() + 3600 * 24 * 7])
    db.commit()


def get_milestone(db, milestone):
    cursor = db.cursor()
    cursor.execute("""
        SELECT name, due, completed, started, description
        FROM milestone WHERE name = %s""", (milestone,))
    mile = cursor.fetchone()
    if mile is not None:
        return {'name': mile[0], 'due': mile[1], 'completed': mile[2],
                'started': mile[3], 'description': mile[4]}
    else:
        return None


def get_milestones(db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT name, due, completed, started, description
        FROM milestone order by name""")
    milestone_lists = cursor.fetchall()
    milestones = []
    for mile in milestone_lists:
        milestones.append(
            {'name': mile[0], 'due': mile[1], 'completed': mile[2],
             'started': mile[3], 'description': mile[4]})
    return milestones


def get_components(db):
    cursor = db.cursor()
    cursor.execute("SELECT name, owner, description FROM component")
    component_lists = cursor.fetchall()
    components = []
    for comp in component_lists:
        components.append(
            {'name': comp[0], 'owner': comp[1], 'description': comp[2]})
    return components


def table_exists(db, table_name):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM %s" % table_name)
    except:
        cursor.connection.rollback()
        return False
    return True


def table_field_exists(db, table_name, field_name):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT %s FROM %s" % (field_name, table_name))
    except:
        cursor.connection.rollback()
        return False
    return True


def get_startdate_for_milestone(db, milestone):
    cursor = db.cursor()
    cursor.execute("SELECT started FROM milestone WHERE name = %s",
                   (milestone,))
    row = cursor.fetchone()
    if row and row[0]:
        return datetime.fromtimestamp(row[0])
    else:
        return None


def set_startdate_for_milestone(db, milestone, startdate):
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE milestone SET started = %s WHERE name = %s",
                       [startdate, milestone])
    except Exception, e:
        print "Error while updating milestone start date, %s" % e
        db.rollback()
        return
    db.commit()


def create_burndown_table(db, env):
    cursor = db.cursor()

    db_backend, _ = DatabaseManager(env)._get_connector()
    for stmt in db_backend.to_sql(burndown_table):
        try:
            cursor.execute(stmt)
        except Exception, e:
            print "Upgrade failed\nSQL:\n%s\nError message: %s" % (stmt, e)
            db.rollback()
            return
    db.commit()


def upgrade_burndown_table(db, env):
    cursor = db.cursor()

    try:
        cursor.execute(
            "CREATE TEMPORARY TABLE burndown_old as SELECT * FROM burndown")
        cursor.execute("DROP TABLE burndown")

        db_backend, _ = DatabaseManager(env)._get_connector()
        for stmt in db_backend.to_sql(burndown_table):
            cursor.execute(stmt)

        cursor.execute("""
            INSERT INTO burndown (id, component_name, milestone_name,
              date, hours_remaining)
            SELECT id, component_name, milestone_name, date, hours_remaining
            FROM burndown_old""")

        db.commit()
    except Exception, e:
        print "Upgrade of the Burndown plugin failed\nError message: %s" % e
        db.rollback()
        return


def upgrade_milestone_table(db, env):
    cursor = db.cursor()

    try:
        cursor.execute(
            "CREATE TEMPORARY TABLE milestone_old as SELECT * FROM milestone")
        cursor.execute("DROP TABLE milestone")

        db_backend, _ = DatabaseManager(env)._get_connector()
        for stmt in db_backend.to_sql(milestone_table):
            cursor.execute(stmt)

        cursor.execute("""
            INSERT INTO milestone(name, due, completed, started, description)
            SELECT name, due, completed, 0, description FROM milestone_old""")

        db.commit()
    except Exception, e:
        print "Upgrade of the Burndown plugin failed\nError message: %s" % e
        db.rollback()
        return
