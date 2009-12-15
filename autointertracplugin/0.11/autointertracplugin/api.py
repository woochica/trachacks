import trac, trac.core,  trac.env, trac.config, os, os.path, urlparse



class AutoInterTracPluginSetupParticipant(trac.core.Component):
    """ 
    This component monkey patches env.setup_config to add configuration
      keys to in memory config that expresses all of the intertrac linkings
      for a directory of trac instances. Also overrides config.save so that 
      these autofilled values are not written to disk.  This prevents these 
      keys from ever being out of date with what is on disk.
      
    Expects the [intertrac] keys base_dir and base_url which should specify 
      a folder of trac instances and their standard url (generally 
      something like http://trac.mydomain.com/ which will result in links like:
      http://trac.mydomain.com/MyProjectName/ticket/33
    
    """
    trac.core.implements(trac.env.IEnvironmentSetupParticipant)
    # add auto config vars when we read in the config
    def run_setup (self):
      original_setup = trac.env.Environment.setup_config
      original_save = trac.config.Configuration.save
      autointertrac = self
      self.hash = {}
      def setup_config(self, load_defaults=False):
        autointertrac.log.debug("AutoInterTrac: setup")
        original_setup(self, load_defaults)
        c = self.config
        base_dir = c.get("intertrac", "base_dir")
        base_url = c.get("intertrac", "base_url")
        if not base_dir or not base_url:
          return
        try:
          (root, kiddirs, files) = os.walk(base_dir).next()
        except:
          self.log.exception("failed to read base_dir:%s"%base_dir)
          return
        for (path, kd) in [(os.path.join(root, kd), kd) for kd in kiddirs]:
          # looks like a trac env
          if os.path.exists(os.path.join(path,'VERSION')):  
            autointertrac.hash[kd] = kd
            c.set("intertrac", kd, kd )
            c.set("intertrac", "%s.title"%kd, kd )
            c.set("intertrac", "%s.url"%kd, urlparse.urljoin(base_url,kd))
            c.set("intertrac", "%s.compat"%kd, "false")

      #remove auto added config vars
      def save(self):
        autointertrac.log.debug("AutoInterTrac: save")
        for key in hash.keys():
          c.remove("intertrac", key)
          c.remove("intertrac", "%s.title"%key)
          c.remove("intertrac", "%s.url"%key)
          c.remove("intertrac", "%s.compat"%key)
        original_save(self)
      trac.env.Environment.setup_config = setup_config
      trac.config.Configuration.save = save
      self.env.setup_config()
      


    def __init__(self):
      #only if we should be enabled do we monkey patch
      if self.compmgr.enabled[self.__class__]:
        self.run_setup()
    def environment_created(self):
      """Called when a new Trac environment is created."""
      pass

    def environment_needs_upgrade(self, db):
      """Called when Trac checks whether the environment needs to be upgraded.
      
      Should return `True` if this participant needs an upgrade to be
      performed, `False` otherwise.
      
      """
      pass

    def upgrade_environment(self, db):
      """Actually perform an environment upgrade.

      Implementations of this method should not commit any database
      transactions. This is done implicitly after all participants have
      performed the upgrades they need without an error being raised.
      """
      pass        

    
