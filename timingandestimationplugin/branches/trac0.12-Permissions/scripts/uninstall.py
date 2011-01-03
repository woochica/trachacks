#!/usr/bin/python
### Warning removes all trace of T&E from your computer ###
### USE ONLY IN DIREST NEED AND WITH CAUTION            ###

import re,shutil,traceback
from optparse import OptionParser
from trac.env import Environment

parser = OptionParser("""usage: [options] trac-install
    trac-install <- The path to your trac install.""")

def p(question):
    return raw_input('%s\nT&E-uninstall> '%question)

def cast_bool(s):
    return len(re.findall('(?i)(y|t|1)', s))>0

def p_bool(question):
    return cast_bool(raw_input('%s\nT&E-uninstall> '%question))

field_list = ['estimatedhours', 'hours', 'billable', 'totalhours', 'internal']
fields = "'estimatedhours', 'hours', 'billable', 'totalhours', 'internal'"

class Script ( object ):
    def __init__(self):
        while self.find_and_remove_installs():pass
        (options,args) = parser.parse_args()
        if(len(args) == 0) :
            self.trac= p('Please type your trac path (or run this script passing it the path):')
        else:
            self.trac = args[0]
        print "Opening trac environment"
        self.env = Environment(self.trac)
        self.env.with_transaction()

        print "Removing T&E from trac env"
        self.find_and_remove_custom_vars()
        self.find_and_remove_ticket_change()
        self.find_and_remove_reports()
        self.remove_configuration()
        self.remove_system_keys()
        print "Done uninstalling"
        

    def execute_in_trans(self, *args):
        result = True
        c_sql =[None]
        c_params = [None]
        @self.env.with_transaction()
        def fn(db):
            try:
                cur = db.cursor()
                for sql, params in args:
                    c_sql[0] = sql
                    c_params[0] = params
                    cur.execute(sql, params)
            except Exception, e :
                print 'There was a problem executing sql:%s \n \
        with parameters:%s\nException:%s'%(c_sql[0], c_params[0], e);
                raise e
        return result

    def execute(self, sql, *params):
        """Executes the query on the given project"""
        self.execute_in_trans((sql, params))

    def get_first_row(self, sql,*params):
        """ Returns the first row of the query results as a tuple of values (or None)"""
        db = self.env.get_read_db()
        cur = db.cursor()
        data = None;
        try:
            cur.execute(sql, params)
            data = cur.fetchone();
        except Exception, e:
            print 'There was a problem executing sql:%s \n \
        with parameters:%s\nException:%s'%(sql, params, e)
        return data;


    def find_and_remove_installs(self):
        try:
            import timingandestimationplugin
            path = timingandestimationplugin.__file__
            install_path = re.findall( '^.*egg', path)
            if len(install_path)>0:
                install_path = install_path[0]
            else:
                print "Cant remove this install: %s" % install_path
                return False
            if p_bool('Remove: %s (y/n)'%install_path):
                shutil.rmtree(install_path)
                return true #could be true, but just run it more than once
            return False
        except ImportError:
            return False

    def find_and_remove_custom_vars(self):
        try:
            if self.get_first_row("SELECT * FROM ticket_custom WHERE name in (%s)"%fields):
                if p_bool("Remove custom fields (%s) (y/n)"%fields):
                    self.execute('DELETE FROM ticket_custom WHERE name in (%s)'%fields)
        except Exception,e:
            print "Failed to remove ticket_custom",e
            traceback.print_exc()

    def find_and_remove_ticket_change(self):
        try:
            if self.get_first_row("SELECT * FROM ticket_change WHERE field in (%s)"%fields):
                if p_bool("Remove ticket changes (%s) (y/n)"%fields):
                    self.execute('DELETE FROM ticket_change WHERE field in (%s)'%fields)
        except Exception,e:
            print "Failed to remove ticket_changes",e
            traceback.print_exc()

    def find_and_remove_reports(self):
        try:
            if self.get_first_row(
                "SELECT * FROM report WHERE id in ("
                "SELECT id FROM custom_report WHERE "
                "maingroup='Timing and Estimation Plugin')"):
                if p_bool("Remove T&E reports  (y/n)"):
                    self.execute("DELETE FROM report WHERE id in ("
                                 "SELECT id FROM custom_report WHERE "
                                 "maingroup='Timing and Estimation Plugin')")
                    self.execute("DELETE FROM custom_report WHERE "
                                 "maingroup='Timing and Estimation Plugin'")

        except Exception,e:
            print "Failed to remove reports",e
            traceback.print_exc()

    def remove_configuration(self):
        if not p_bool('Remove T&E configuration (y/n)'): return
        for k,v in self.env.config.options('ticket-custom'):
            if any(re.search('(?i)'+f,k) for f in field_list):
                self.env.config.remove('ticket-custom',k)
        for k,v in self.env.config.options('field settings'):
            self.env.config.remove('field settings',k)

        for k,v in self.env.config.options('components'):
            if re.search('timingandestimationplugin',k):
                self.env.config.remove('components', k);

        for k,v in self.env.config.options('field settings'):
            self.env.config.remove('field settings',k)

        if re.search('InternalTicketsPolicy', 
                      self.env.config.get('trac','permission_policies','')):
            print "Please remove InternalTicketsPolicy from your trac.ini [trac] permission_policies"
        self.env.config.save()

    def remove_system_keys(self):
        if not p_bool('Remove T&E system keys'): return 
        self.execute("DELETE FROM system WHERE name in "
                     "('TimingAndEstimationPlugin_Db_Version','T&E-statuses');")



if __name__ == '__main__' :
    Script()
