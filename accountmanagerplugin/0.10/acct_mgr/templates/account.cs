<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="register">

 <h1>My Account</h1>

 <p>
 Manage your user account.
 </p>

 <?cs if account.error ?>
 <div class="system-message">
  <h2>Error</h2>
  <p><?cs var:account.error ?></p>
 </div>
 <?cs /if ?>

 <?cs if account.message ?>
 <p><?cs var:account.message ?></p>
 <?cs /if ?>

 <h2>Change Password</h2>
 <?cs if account.save_error ?>
 <div class="system-message">
  <h2>Error</h2>
  <p><?cs var:account.save_error ?></p>
 </div>
 <?cs /if ?>

 <form method="post" action="">
  <input type="hidden" name="action" value="change_password" />
  <div>
   <label for="old_password">Old Password:</label>
   <input type="password" id="old_password" name="old_password"
          class="textwidget" size="20" />
  </div>
  <div>
   <label for="password">New Password:</label>
   <input type="password" id="password" name="password" class="textwidget"
          size="20" />
  </div>
  <div>
   <label for="password_confirm">Confirm Password:</label>
   <input type="password" id="password_confirm" name="password_confirm"
          class="textwidget" size="20" />
  </div>
  <input type="submit" value="Change password" />
 </form>

 <?cs if:delete_enabled ?>
 <hr />

 <h2>Delete Account</h2>
 <?cs if account.delete_error ?>
 <div class="system-message">
  <h2>Error</h2>
  <p><?cs var:account.delete_error ?></p>
 </div>
 <?cs /if ?>

 <form method="post" action=""
       onsubmit="return confirm('Are you sure you want to delete your account?');">
  <input type="hidden" name="action" value="delete" />
  <div>
   <label for="password">Password:</label>
   <input type="password" id="password" name="password" class="textwidget"
          size="20" />
  </div>
  <input type="submit" value="Delete account" />
 </form>
 <?cs /if ?>

</div>

<?cs include:"footer.cs"?>
