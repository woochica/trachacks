<h2>Manage Permissions</h2>

<?cs def:hdf_select(options, name, selected, optional) ?>
 <select size="1" id="<?cs var:name ?>" name="<?cs var:name ?>"><?cs
  if:optional ?><option></option><?cs /if ?><?cs
  each:option = options ?>
   <option<?cs if:option == selected ?> selected="selected"<?cs /if ?>><?cs 
     var:option ?></option><?cs
  /each ?>
 </select><?cs
/def?>
<form id="addperm" class="addnew" method="post">
 <fieldset>
  <legend>Grant Permission:</legend>
  <div class="field">
   <label>Subject: <input type="text" name="subject" /></label>
  </div>
  <div class="field">
   <label>Action: <?cs call:hdf_select(admin.actions, "action", "", 0) ?></label>
  </div>
  <p class="help">Grant permission for an action to a subject, which can be
  either a user or a group.</p>
  <div class="buttons">
   <input type="submit" name="add" value=" Add ">
  </div>
 </fieldset>
</form>

<form id="addsubj" class="addnew" method="post">
 <fieldset>
  <legend>Add Subject to Group:</legend>
  <div class="field">
   <label>Subject: <input type="text" name="subject" /></label>
  </div>
  <div class="field">
   <label>Group: <input type="text" name="group" /></label>
  </div>
  <p class="help">Add a user or group to an existing permission group.</p>
  <div class="buttons">
   <input type="submit" name="add" value=" Add ">
  </div>
 </fieldset>
</form>

<form method="post">
 <table class="listing" id="permlist">
  <thead>
   <tr><th class="sel">&nbsp;</th><th>Subject</th><th>Action</th></tr>
  </thead><tbody><?cs
  each:perm = admin.perms ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:perm.key ?>" /></td>
    <td><?cs var:perm.subject ?></td>
    <td><?cs var:perm.action ?></td>
   </tr><?cs
  /each ?></tbody>
 </table>
 <div class="buttons">
  <input type="submit" name="remove" value="Remove selected items" />
 </div>
</form>
