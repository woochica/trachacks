= About this software =
 * Trac Image SVG macro is a Trac plugin/macro.

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall Trac Image SVG macro if you have installed before.

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
imagesvg.* = enabled
}}}

= Usage =
 1. Upload svg files to wiki or ticket, eg: example.svg
 1. Display svg image inwiki page !TopPage/SubPage
  * Display right in !TopPage/SubPage: 
   {{{
[[ImageSvg(example.svg)]]
}}}
  * Display in other pages or tickets: 
   {{{
[[ImageSvg(wiki:TopPage/SubPage:example.svg)]]
}}}
 1. Display svg image in ticket 123 which has attachment example.svg
   {{{
[[ImageSvg(example.svg)]]
}}}
  * Display in other wiki pages or tickets which reference svg attachment of ticket 123: 
   {{{
[[ImageSvg(ticket:123:example.svg)]]
}}}