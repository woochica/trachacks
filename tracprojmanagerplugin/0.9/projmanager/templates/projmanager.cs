<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="projmanager">
 <div id="ctxtnav"></div>

 <h1>Project Management</h1>

 <div class="tabs"><?cs set:cur_cat_id = '' ?><ul><?cs
  each:page = projmanager.pages ?><?cs
   if:page.cat_id != cur_cat_id ?><?cs
     if:name(page) != 0 ?></ul></li><?cs
     /if ?><li<?cs
     if:page.cat_id == projmanager.active_cat ?> class="active"<?cs
     /if ?>><?cs var:page.cat_label ?><ul><?cs
   /if ?><?cs
   if:page.page_id == projmanager.active_page ?><li class="active"><a href="<?cs var:page.href ?>"><?cs
     var:page.page_label ?></a></li><?cs
   else ?><li><a href="<?cs var:page.href ?>"><?cs
     var:page.page_label ?></a></li><?cs
   /if ?><?cs
   set:cur_cat_id = page.cat_id ?><?cs
  /each ?></ul><li/></ul>
 </div>

 <div class="tabcontents">
  <?cs include projmanager.page_template ?>
  <br style="clear: right"/>
 </div>
</div>

<?cs include "footer.cs"?>
