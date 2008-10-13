= About this software =
 * http://trac-hacks.org/wiki/TracTweakUI
 * Trac Tweak UI is a Trac plugin.
 * Its purpose is to implement a javascript deployment platform, which enable trac administrators to easy tweak trac pages simply using javascript.
 * It can apply different javascripts to different pages by matching regular expression.

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall Trac Tweak UI if you have installed before.

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
tractweakui.* = enabled
}}}

 6. Add following directory structure to trac environment's htdocs directory(using editcc as example):
  {{{
htdocs/tractweakui/
}}}

Or you can simply copy the htdocs/tractweakui/ in source to trac environment's htdocs directory.

= Usage =
 1. Enter trac's web admin, select "TracTweakUI Admin"
 1. Add url path(regular expression): ^/newticket
 1. Select "^/newticket", then select filter "editcc"
 1. Click "Load Default", and edit filter javascript, then "Save"
 1. Now click "New Ticket" to test the "editcc" javascript plugin.
