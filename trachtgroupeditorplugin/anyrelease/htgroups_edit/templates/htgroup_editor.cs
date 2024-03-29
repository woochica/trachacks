<h2>Manage HTGroup file</h2>

<?cs if:!listing_enabled ?>
 <div class="system-message">
  <p>There are no groups defined. Use the add dialog to insert new users/groups.</p>
 </div>
 <br/>
<?cs /if ?>    
<?cs if: message ?>
 <div class="system-message">
  <p><?cs var:message ?></p>
 </div>
 <br/>
<?cs /if ?>    

<form id="addsubj" class="addnew" method="post">
 <input type="hidden" name="group" value="<?cs var:group ?>" />
 <fieldset>
  <legend>Add User to Group:</legend>
  <div class="field">
   <label>User: <input type="text" name="new_user" /></label>
  </div>
  <div class="field">
   <label>Group: <input type="text" name="new_group" value="<?cs var:group ?>" /></label>
  </div>
  <p class="help">Add a user to an existing or new group.</p>
  <div class="buttons">
   <input type="submit" name="add" value=" Add ">
  </div>
 </fieldset>
</form>


<?cs if: selection_enabled ?>
 <form name="groupselection" method="post">
  Select group:
  <select size=1 name="group" onChange="document.groupselection.submit()">
   <thread>
     <?cs each:one_group=groups ?>
       <?cs if: one_group==group ?><option selected><?cs else ?><option><?cs /if ?><?cs var:one_group ?></option>
     <?cs /each ?>
   </thread>
  </select>
  <input type="submit" name="update" value="Refresh list" />
 </form>
<?cs /if ?>

<?cs if: listing_enabled ?>
 <h2>Editing group: <i><?cs var:group ?></i></h2>
 <form method="post">
  <input type="hidden" name="group" value="<?cs var:group ?>" />
  <table class="listing" id="grouplist">
   <thead>
    <tr><th class="sel">&nbsp;</th><th>User</th></tr>
   </thead><tbody><?cs
   each:user = members ?>
    <tr>
     <td><input type="checkbox" name="sel" value="<?cs var:user ?>" /></td>
     <td><?cs var:user ?></td>
    </tr><?cs
   /each ?></tbody>
  </table>
  <div class="buttons">
   <input type="submit" name="remove" value="Remove selected users from '<?cs var:group ?>'" />
  </div>
 </form>
<?cs /if ?>
