# -*- encoding: UTF-8 -*-

'''
Created on 12 oct. 2010

@author: thierry
'''
from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from threading import Timer



class ICronTask(Interface):
    """
    Interface for component task
    """
    
    def wake_up(self):
        raise NotImplementedError
    
    def getId(self):
        raise NotImplementedError


class Core(Component):    
    """
    Main class of the Trac Cron Plugin. This is the entry point
    for Trac plugin architecture
    """    
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    cron_tack_list = ExtensionPoint(ICronTask)
    
    
    def __init__(self,*args,**kwargs):
        """
	    Intercept the instanciation to start the ticker
        """        
        Component.__init__(self, *args, **kwargs)
        self.cronconf = CronConfig(self.env)
        self.webUi = WebUi(self.env)        
        self.apply_config()
        
    def apply_config(self):
        """
        Read configuration and apply it
        """
        if self.getCronConf().get_ticker_enabled():
        	self.ticker = Ticker(self.getCronConf().get_ticker_enabled(), self.check_task)

    def getCronConf(self):
        """
        Return the configuration for TracCronPlugin
        """
        return self.cronconf
    
    def check_task(self):
        """
        Check if any task need to be executed. This method is called by the Ticker.
        """
        # store current time
        
        for task in self.cron_tack_list:
            # test current time with task planing
            
            # run task if needed
            pass

        
    # IAdminPanel interface
    
    def get_admin_panels(self, req):
       return self.webUi.get_admin_panels(req)


    def render_admin_panel(self, req, category, page, path_info):
        return self.webUi.render_admin_panel(req, category, page, path_info)

    # ITemplateProvider interface
    def get_htdocs_dirs(self):
        return self.webUi.get_htdocs_dirs()


    def get_templates_dirs(self):
       return self.webUi.get_templates_dirs()
    
        
        
 
class CronConfig():
    """
    This class read and write configuration for TracCronPlugin
    """
    TRACCRON_SECTION = "traccron"
    
    TICKER_ENABLED_KEY = "ticker.enabled"
    TICKER_ENABLED_DEFAULT = "False"
    
    TICKER_INTERVAL_KEY = "ticker.interval"
    TICKER_INTERVAL_DEFAULT = 1 #minutes
    

    def __init__(self, env):
        self.env = env
            
    def get_ticker_enabled(self):
        return self.env.config.getbool(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, self.TICKER_ENABLED_DEFAULT)

    def set_ticker_enabled(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, value)


class WebUi(IAdminPanelProvider, ITemplateProvider):
    """
    Class that deal with Web stuff. It is the both the controller and the page builder.
    """
    def __init__(self, env):
        self.env = env
    
    def get_admin_panels(self, req):
        if ('TRAC_ADMIN' in req.perm) :
            yield ('tracini', 'trac.ini', 'cron_admin', u'Trac Cron')


    def render_admin_panel(self, req, category, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        data = {}
        
        if req.method == 'POST':
            if 'save' in req.args:                                
                req.redirect(req.abs_href.admin(category, page))
        else:            
            return 'cron_admin.html', data

    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]




class Ticker():
    """
    A Ticker is simply a simply timer that will repeatly wake up.
    """
    
    
    def __init__(self, env, interval, callback):
        """
        Create a new Ticker.
        env : the trac environnement
        interval: interval in second
        callback: the function callback to call o every wake-up
        """
        self.env = env
        self.interval
        self.callback = callback
        self.timer = None
        self.create_new_timer()
        
    def create_new_timer(self, wait=False):
        """
        Create a new timer before killing existing one if required.
        wait : if True the current thread wait until running task finished. Default is False
        """
        if (self.timer != None):
            self.timer.cancel()
            if ( wait ):
                self.timer.join()            
        
        self.timer = Timer(self.interval, self.wake_up)
        self.timer.start()

    def wake_up(self):
        self.callback()
        self.create_new_timer()


class HeartBeatTask(Component,ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log a debug levem
    """
    
    implements(ICronTask)
    
    def wake_up(self):
        self.env.log.debug("Heart beat: boom boom")
    
    def getId(self):
        return "heart_beat"
    
    