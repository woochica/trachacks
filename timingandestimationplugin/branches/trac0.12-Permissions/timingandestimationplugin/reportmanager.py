from trac.core import *
import dbhelper

def tryint(val, default=0):
  if not val: return default
  try:
    return int(val)
  except ValueError:
    return default

class CustomReportManager:
  """A Class to manage custom reports"""
  version = 1
  name = "custom_report_manager_version"
  env = None
  log = None
  TimingAndEstimationKey = "Timing and Estimation Plugin"
  
  def __init__(self, env, log):
    self.env = env
    self.log = log
    self.upgrade()

  def upgrade(self):
    self.env.log.debug("T&E Starting Report Schema Upgrade")
    # Check to see what version we have
    version = tryint(dbhelper.get_system_value(self.env, self.name))
    if version > self.version:
      raise TracError("Fatal Error: You appear to be running two plugins with"
                      " conflicting versions of the CustomReportManager class."
                      " Please ensure that '%s' is updated to "
                      "version %s of the file reportmanager.py (currently using version %s)."
                      % (__name__, str(self.version), str(version)))

      # Do the staged updates
    if version < 1:
      dbhelper.execute_non_query(
        self.env,
        "CREATE TABLE custom_report ("
        "id         INTEGER,"
        "uuid       VARCHAR(64),"
        "maingroup  VARCHAR(255),"
        "subgroup   VARCHAR(255),"
        "version    INTEGER,"
        "ordering   INTEGER)")
      
        #if version < 2:

    # Updates complete, set the version
    dbhelper.set_system_value(self.env, self.name, self.version)
    self.env.log.debug("T&E Ending Report Schema Upgrade")

  def get_report_id_and_version (self, uuid):
    sql = "SELECT custom_report.id, custom_report.version FROM custom_report "\
        "JOIN report ON report.id = custom_report.id " \
        "WHERE uuid=%s"
    tpl = dbhelper.get_first_row(self.env, sql, uuid)
    return tpl or (None, 0)
    
  def get_new_report_id (self):
    """find the next available report id """
    rtn = dbhelper.get_scalar(self.env, "SELECT MAX(id) FROM report")
    return (rtn and rtn+1) or 1
    
  def get_max_ordering(self, maingroup, subgroup):
    """ Find the maximum ordering value used for this group of the custom_report table"""
    return dbhelper.get_scalar(self.env, "SELECT MAX(ordering) FROM custom_report WHERE maingroup=%s AND subgroup=%s",
                           0, maingroup, subgroup) or 0
  
  def _insert_report (self, next_id, title, author, description, query,
                      uuid, maingroup, subgroup, version, ordering):
    """ Adds a row the custom_report_table """
    self.log.debug("Inserting new report '%s' with uuid '%s'" % (title,uuid))
    dbhelper.execute_in_trans(
      self.env,
      ("DELETE FROM custom_report WHERE uuid=%s", (uuid,)), 
      ("INSERT INTO report (id, title, author, description, query) " \
         "VALUES (%s, %s, %s, %s, %s)",
       (next_id, title, author, description, query)),
      ("INSERT INTO custom_report (id, uuid, maingroup, subgroup, version, ordering) " \
         "VALUES (%s, %s, %s, %s, %s, %s)",
       (next_id, uuid, maingroup, subgroup, version, ordering)))
    self.log.debug("Attempting to increment sequence (only works in postgres)")
    if type(e.get_read_db().cnx) == trac.db.postgres_backend.PostgreSQLConnection:
      try:
        dbhelper.execute_in_nested_trans(self.env, "update_seq", ("SELECT nextval('report_id_seq');",[]));
        self.log.debug("Sequence updated");
      except:
        self.log.debug("Sequence failed to update, perhaps you are not running postgres?");

  def _update_report (self, id, title, author, description, query,
                      maingroup, subgroup, version):
    """Updates a report and its row in the custom_report table """
    self.log.debug("Updating report '%s' with to version %s" % (title, version))
    dbhelper.execute_in_trans(
      self.env,
      ("UPDATE report SET title=%s, author=%s, description=%s, query=%s " \
         "WHERE id=%s", (title, author, description, query, id)),
      ("UPDATE custom_report SET version=%s, maingroup=%s, subgroup=%s "
       "WHERE id=%s", (version, maingroup, subgroup, id)))
    
  def add_report(self, title, author, description, query, uuid, version,
                 maingroup, subgroup="", force=False):
    """
    We add/update a report to the system. We will not overwrite unchanged versions
    unless force is set.
    """
    # First check to see if we can load an existing version of this report
    (id, currentversion) = self.get_report_id_and_version(uuid)
    self.log.debug("add_report %s (ver:%s) | id: %s currentversion: %s" % (uuid , version, id, currentversion))
    try:
      if not id:
        next_id = self.get_new_report_id()
        ordering = self.get_max_ordering(maingroup, subgroup) + 1
        self._insert_report(next_id, title, author, description, query,
                      uuid, maingroup, subgroup, version, ordering)
        return True
      if currentversion < version or force:
        self._update_report(id, title, author, description, query,
                            maingroup, subgroup, version)
        return True
    except Exception, e:
      self.log.error("CustomReportManager.add_report Exception: %s, %s" % (e,(title, author, uuid, version,
                 maingroup, subgroup, force)));
    self.log.debug("report %s not upgraded (a better version already exists)" % uuid)
    return False
  
  def get_report_by_uuid(self, uuid):
    sql = "SELECT report.id,report.title FROM custom_report "\
          "LEFT JOIN report ON custom_report.id=report.id "\
          "WHERE custom_report.uuid=%s"
    return dbhelper.get_first_row(self.env, sql,uuid)

  def get_reports_by_group(self, group):
    """Gets all of the reports for a given group"""
    rv = {}
    try:
      res = dbhelper.get_result_set(
        self.env, 
        "SELECT custom_report.subgroup,report.id,report.title,"
        " custom_report.version, custom_report.uuid "
        "FROM custom_report "
        "LEFT JOIN report ON custom_report.id=report.id "
        "WHERE custom_report.maingroup=%s "
        "ORDER BY custom_report.subgroup,custom_report.ordering", group)
      if not res:
        return rv
      for subgroup, id, title, version, uuid in res.rows:
        if not rv.has_key(subgroup):
          rv[subgroup] = { "title": subgroup,
                           "reports": [] }
        rv[subgroup]["reports"].append( { "id": int(id), "title": title, "version":version, "uuid":uuid } )
    except:
      self.log.exception("Error getting reports by group")
    return rv
  
  def get_version_hash_by_group(self, group):
    """Gets all of the reports for a given group as a uuid=>version hash"""
    rv = {}
    try:
      res = dbhelper.get_result_set(
        self.env, 
        "SELECT custom_report.subgroup,report.id,report.title,"
        " custom_report.version, custom_report.uuid "
        "FROM custom_report "
        "LEFT JOIN report ON custom_report.id=report.id "
        "WHERE custom_report.maingroup=%s "
        "ORDER BY custom_report.subgroup,custom_report.ordering",
        group)
      if not res:
        return rv;
      for subgroup, id, title, version, uuid in res.rows:
        rv[uuid] = version
    except:
      self.log.exception("Failed to get_version_hash_by_group")
    return rv
