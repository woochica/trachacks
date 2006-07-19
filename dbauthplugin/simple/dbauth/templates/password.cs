<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<style type="text/css">
  input[type=password] { border: 1px solid #d7d7d7 }
  input[type=password] { padding: .25em .5em }
  input[type=password]:focus { border: 1px solid #886 }

  .message {color: red; font-weight: bold;}
</style>

<h2>Change Password</h2><?cs
  if:auth.message ?><p class="message"><?cs
    var:auth.message ?></p><?cs
  /if ?>

<form method="post">
  <table>
    <tr><td>Old Password:</td><td><input id="opwd" name="opwd" type="password"/></td></tr>
    <tr><td>New Password:</td><td><input id="npwd" name="npwd" type="password"/></td></tr>
    <tr><td>Repeat Password:</td><td><input id="rpwd" name="rpwd" type="password"/></td></tr>
  </table>
  <div class="buttons">
    <input type="submit" name="password" value="Change" />
    <input type="submit" name="cancel" value="Cancel" />
  </div>
</form>

<script type="text/javascript">
  var uid = document.getElementById("opwd");
  uid.focus();
  uid.select();
</script> 

<?cs include:"footer.cs"?>
