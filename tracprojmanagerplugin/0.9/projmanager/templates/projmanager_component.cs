<h2>Manage Components</h2><?cs

if:projmanager.component.name ?>
 <form class="mod" id="modcomp" method="post">
  <fieldset>
   <legend>Modify Component:</legend>
   <div class="field">
    <label>Name:<br /><input type="text" name="name" value="<?cs
      var:projmanager.component.name ?>" /></label>
   </div>
   <div class="field">
    <label>Owner:<br /><?cs
     if:len(projmanager.owners) ?><?cs
      call:hdf_select(projmanager.owners, "owner", "", 0) ?><?cs
     else ?><input type="text" name="owner" value="<?cs
      var:projmanager.component.owner ?>" /><?cs
     /if ?></label>
   </div>
   <div class="field">
    <fieldset class="iefix">
     <label for="description">Description (you may use <a tabindex="42" href="<?cs
       var:trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label>
     <p><textarea id="description" name="description" class="wikitext" rows="6" cols="60"><?cs
       var:projmanager.component.description ?></textarea></p>
    </fieldset>
   </div>
   <script type="text/javascript" src="<?cs
     var:chrome.href ?>/common/js/wikitoolbar.js"></script>
   <div class="buttons">
    <input type="submit" name="cancel" value="Cancel" />
    <input type="submit" name="save" value="Save" />
   </div>
  </fieldset>
 </form><?cs

else ?>
 <form class="addnew" id="addcomp" method="post">
  <fieldset>
   <legend>Add Component:</legend>
   <div class="field">
    <label>Name:<br /><input type="text" name="name" /></label>
   </div>
   <div class="field">
    <label>Owner:<br /><?cs
     if:len(projmanager.owners) ?><?cs
      call:hdf_select(projmanager.owners, "owner", "", 0) ?><?cs
     else ?><input type="text" name="owner" /><?cs
     /if ?></label>
   </div>
   <div class="field">
    <fieldset class="iefix">
     <label for="description">Description (you may use <a tabindex="42" href="<?cs
       var:trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label>
     <p><textarea id="description" name="description" class="wikitext" rows="3" cols="35"></textarea></p>
    </fieldset>
   </div>
   <script type="text/javascript" src="<?cs
     var:chrome.href ?>/common/js/wikitoolbar.js"></script>
   <div class="buttons">
    <input type="submit" name="add" value="Add">
   </div>
  </fieldset>
 </form><?cs

 if:len(projmanager.components) ?><form method="POST">
  <table class="listing" id="complist">
   <thead>
    <tr><th class="sel">&nbsp;</th><th>Name</th>
    <th>Owner</th></tr>
   </thead><?cs
   each:comp = projmanager.components ?>
    <tr>
     <td class="sel"><input type="checkbox" name="sel" value="<?cs var:comp.name ?>" /></td>
     <td><a href="<?cs var:comp.href?>"><?cs var:comp.name ?></a></td>
     <td><?cs var:comp.owner ?></td>
    </tr><?cs
   /each ?>
  </table>
  <div class="buttons">
   <input type="submit" name="remove" value="Remove selected items" />
  </div>
  <p class="help">You can remove all items from this list to completely hide
  this field from the user interface.</p>
 </form><?cs
 else ?>
  <p class="help">As long as you don't add any items to the list, this field
  will remain completely hidden from the user interface.</p><?cs
 /if ?><?cs

/if ?>
