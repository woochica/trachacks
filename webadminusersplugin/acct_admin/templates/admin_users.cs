<h2>Manage Users</h2>

<?cs if users.error ?>
 <div class="system-message">
  <?cs var:users.error ?>
 </div>
<?cs /if ?>

<form id="adduser" class="addnew" method="post">
 <fieldset>
  <legend>Add User:</legend>
  <div class="field">
   <label>Username: <input type="text" name="username" /></label>
  </div>
  <div class="field">
   <label>Password: <input type="password" name="password1" /></label>
  </div>
  <div class="field">
   <label>Confirm: <input type="password" name="password2" /></label>
  </div>
  <p class="help">Register a user</p>
  <div class="buttons">
   <input type="submit" name="add" value=" Add " />
  </div>
 </fieldset>
</form>

<form method="post">
 <table class="listing" id="userlist">
  <thead>
   <tr><th class="sel">&nbsp;</th><th>User</th></tr>
  </thead>
  <tbody>
  <?cs each:user = admin.users ?>
   <tr>
    <td class="sel">
     <input type="checkbox" name="sel" value="<?cs var:user.key ?>" />
    </td>
    <td class="name">
     <a href="<?cs var:user.href ?>"><?cs var:user.name ?></a>
    </td>
   </tr>
  <?cs /each ?>
  </tbody>
 </table>
 <div class="buttons">
  <input type="submit" name="remove" value="Remove selected users" />
 </div>
</form>
