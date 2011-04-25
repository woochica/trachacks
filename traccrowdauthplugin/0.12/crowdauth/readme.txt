= About this software =
 * http://trac-hacks.org/wiki/TracCrowdAuthPlugin
 * TracCrowdAuthPlugin is a [http://www.atlassian.com/software/crowd crowd] auth store for [http://trac-hacks.org/wiki/AccountManagerPlugin AccountManagerPlugin

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall TracCrowdAuthPlugin if you have installed before.

 2. Change to the directory containning setup.py.

 3. If you want to install this plugin globally, that will install this plugin to the python path:
  * python setup.py install

 4. If you want to install this plugin to trac instance only:
  * python setup.py bdist_egg
  * copy the generated egg file to the trac instance's plugin directory
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. Config trac.ini:
  {{{
[components]
acct_mgr.web_ui.loginmodule = enabled
acct_mgr.web_ui.registrationmodule = disabled
trac.web.auth.loginmodule = disabled

[crowdauth]
crowd_rest_base_url = http://crowdserver:8095/crowd/rest/usermanagement/latest/
crowd_realm = Crowd REST Service
crowd_useranme = trac
crowd_password = trac
crowd_group = trac_grp

[account-manager]
password_store = CrowdAuthStore
}}}

= Prerequisite =
 * [http://trac-hacks.org/wiki/AccountManagerPlugin AccountManagerPlugin]
 * simplejson when using python below 2.6

= Usage =
 * TBD
