from setuptools import setup

PACKAGE = 'autointertracplugin'

setup(name=PACKAGE,
      version='0.0.2',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/AutoInterTracPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
        Automatically make InterTrac link configuration to directories full of trac instances.

        One component: AutoInterTracPluginSetupParticipant
            This component monkey patches env.setup_config to add configuration
            keys to in memory config that expresses all of the intertrac linkings
            for a directory of trac instances. Also overrides config.save so that 
            these autofilled values are not written to disk.  This prevents these 
            keys from ever being out of date with what is on disk.
      
        Expects the [intertrac] keys base_dir and base_url which should specify 
            a folder of trac instances and their standard url (generally 
            something like http://trac.mydomain.com/ which will result in links like:
            http://trac.mydomain.com/MyProjectName/ticket/33

      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

