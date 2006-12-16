<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head><?cs
 if:project.name_encoded ?>
 <title><?cs if:title ?><?cs var:title ?> - <?cs /if ?><?cs
   var:project.name_encoded ?> - Trac</title><?cs
 else ?>
 <title>Trac: <?cs var:title ?></title><?cs
 /if ?><?cs
 if:html.norobots ?>
 <meta name="ROBOTS" content="NOINDEX, NOFOLLOW" /><?cs
 /if ?><?cs
 each:rel = chrome.links ?><?cs
  each:link = rel ?><link rel="<?cs
   var:name(rel) ?>" href="<?cs var:link.href ?>"<?cs
   if:link.title ?> title="<?cs var:link.title ?>"<?cs /if ?><?cs
   if:link.type ?> type="<?cs var:link.type ?>"<?cs /if ?> /><?cs
  /each ?><?cs
 /each ?><style type="text/css"><?cs include:"site_css.cs" ?></style><?cs
 each:script = chrome.scripts ?>
 <script type="<?cs var:script.type ?>" src="<?cs var:script.href ?>"></script><?cs
 /each ?>
</head>

<?cs def:nav(items, class, filter) ?><?cs
 if:len(items) ?><ul class="<?cs var:class ?>"><?cs
  set:idx = 0 ?><?cs
  set:max = len(items) - 1 ?><?cs
  each:item = items ?><?cs
   set:first = idx == 0 ?><?cs
   set:last = idx == max ?><?cs
   if:filter == 1 && name(item)!='login' && name(item)!='register' || filter == 0?><li<?cs
   if:first || last || item.active ?> class="<?cs
    if:item.active ?>active<?cs /if ?><?cs
    if:item.active && (first || last) ?> <?cs /if ?><?cs
    if:first ?>first<?cs /if ?><?cs
    if:(item.active || first) && last ?> <?cs /if ?><?cs
    if:last ?>last<?cs /if ?>"<?cs
   /if ?>><?cs var:item ?></li><?cs
   /if ?><?cs 
   set:idx = idx + 1 ?><?cs
  /each ?></ul><?cs
 /if ?><?cs
/def ?>

<body>
 <table id="mainPan">
  <tr>
   <td id="leftPan">
    <div id="logoPan">
     <table style="width: 100%; height: 100%">
      <tr>
       <td>
     <?cs
      if:chrome.logo.src ?><a id="logo" href="<?cs
      var:chrome.logo.link ?>"><img src="<?cs var:chrome.logo.src ?>"<?cs
      if:chrome.logo.width ?> width="<?cs var:chrome.logo.width ?>"<?cs /if ?><?cs
      if:chrome.logo.height ?> height="<?cs var:chrome.logo.height ?>"<?cs
      /if ?> alt="<?cs var:chrome.logo.alt ?>" /></a><?cs
      elif:project.name_encoded ?><h1><a href="<?cs var:chrome.logo.link ?>"><?cs
      var:project.name_encoded ?></a></h1><?cs
      /if ?>
       </td>
       <td style="text-align: right; vertical-align: bottom;" class="nav">
        <?cs call:nav(chrome.nav.metanav, '', 0) ?>
       </td>
      </tr>
     </table>
     <hr />
    </div>
    <div id="leftbodyPan">
