<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>
  <title>CC selector window</title>
   <?cs
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
  <body>
    <p>Select CC, then <a href="javascript:window.close();">close</a> this window.</p>
    
    <div id="ccdiv">
      <!-- checkboxes will be inserted here -->
    </div>
    
    <div id="cc_developers" >
      <!-- developer names will be taken from here  -->
      <?cs each:dev = cc_developers ?>
        <var class="cc_dev" title="<?cs var:dev ?>"></var>
      <?cs /each ?>
    </div>
  </body>
</html>
