= About this software =
 * http://trac-hacks.org/wiki/TracAutoCompletePlugin
 * AutoComplete is a Trac plugin. 

= Install =

 '''IMPORTANT''': Please BACKUP you ticket templates if you are upgrading this plugin.

 You can install this software as normal Trac plugin.

 1. Uninstall TracAutoComplete if you have installed before.

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
autocomplete.* = enabled
}}}

 6. Create and edit file /srv/trac/env/conf/username_list.txt
 {{{
user1 [Full Name 1]
user2 [Full Name 2]
}}} 

= Usage =
 * TBD
