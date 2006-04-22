[
invisible (render=includeCS, data="site_header.cs"), 
div (id="banner") [
    div (render=tracProjectLogo, id="header")
]
]
#form
#<form id="search" action="<?cs var:trac.href.search ?>" method="get">
# <?cs if:trac.acl.SEARCH_VIEW ?><div>
#  <label for="proj-search">Search:</label>
#  <input type="text" id="proj-search" name="q" size="10" accesskey="f" value="" />
#  <input type="submit" value="Search" />
#  <input type="hidden" name="wiki" value="on" />
#  <input type="hidden" name="changeset" value="on" />
#  <input type="hidden" name="ticket" value="on" />
## </div><?cs /if ?>
#</form>
#
#<?cs def:nav(items) ?><?cs
# if:len(items) ?><ul><?cs
#  set:idx = 0 ?><?cs
#  set:max = len(items) - 1 ?><?cs
#  each:item = items ?><?cs
#   set:first = idx == 0 ?><?cs
#   set:last = idx == max ?><li<?cs
#   if:first || last || item.active ?> class="<?cs
#    if:item.active ?>active<?cs /if ?><?cs
#    if:item.active && (first || last) ?> <?cs /if ?><?cs
#    if:first ?>first<?cs /if ?><?cs
#    if:(item.active || first) && last ?> <?cs /if ?><?cs
#    if:last ?>last<?cs /if ?>"<?cs
#   /if ?>><?cs var:item ?></li><?cs
#   set:idx = idx + 1 ?><?cs
#  /each ?></ul><?cs
# /if ?><?cs
#/def ?>
#
#<div id="metanav" class="nav"><?cs call:nav(chrome.nav.metanav) ?></div>
##</div>
#
#<div id="mainnav" class="nav"><?cs call:nav(chrome.nav.mainnav) ?></div>
#<div id="main">
