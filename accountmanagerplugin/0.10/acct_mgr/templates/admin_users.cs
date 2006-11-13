<h2>Manage User Accounts</h2>

<?cs if:create_enabled ?>
<form id="addaccount" class="addnew" method="post">
 <fieldset>
  <?cs if registration.error ?>
  <div class="system-message"><p><?cs var:registration.error ?></p></div>
  <?cs /if ?>

  <legend>Add Account:</legend>
  <div class="field">
   <label>Username: <input type="text" name="user" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Password: <input type="password" name="password" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Confirm password: <input type="password" name="password_confirm" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Name: <input type="text" name="name" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Email: <input type="text" name="email" class="textwidget" /></label>
  </div>
  <p class="help">Add a new user account.</p>
  <div class="buttons">
   <input type="submit" name="add" value=" Add ">
  </div>
 </fieldset>
</form>
<?cs /if ?>

<?cs if:!listing_enabled ?>
<div class="system-message">
    <p>This password store does not support listing users</p>
</div>
<?cs else ?>
<form method="post">
 <?cs if:deletion_error ?><div class="system-message"><p><?cs var:deletion_error ?></p></div><?cs /if ?>
 <table class="listing" id="accountlist">
  <thead>
   <tr>
    <?cs if:delete_enabled ?><th class="sel">&nbsp;</th><?cs /if ?>
    <th>Account</th><th>Name</th><th>Email</th><th>Last Login</th>
   </tr>
  </thead><tbody><?cs
  each:account = accounts ?>
   <tr>
    <?cs if:delete_enabled ?>
     <td><input type="checkbox" name="sel" value="<?cs var:account.username ?>" /></td>
    <?cs /if ?>
    <td><?cs var:account.username ?></td>
	<td><?cs var:account.name ?></td>
	<td><?cs var:account.email ?></td>
	<td><?cs var:account.last_visit ?></td>
   </tr><?cs
  /each ?></tbody>
 </table>
 <?cs if:delete_enabled ?>
 <div class="buttons">
  <input type="submit" name="remove" value="Remove selected accounts" />
 </div>
 <?cs /if ?>
</form>
<?cs /if ?>

