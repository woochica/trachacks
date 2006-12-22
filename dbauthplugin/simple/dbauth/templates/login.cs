<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<style type="text/css">
  input[type=password] { border: 1px solid #d7d7d7 }
  input[type=password] { padding: .25em .5em }
  input[type=password]:focus { border: 1px solid #886 }

  .message {color: red; font-weight: bold;}
</style>

<h2>Login</h2><?cs
  if:auth.message ?><p class="message"><?cs
    var:auth.message ?></p><?cs
  /if ?>
<form method="post">
  <table>
    <tr><td>Username:</td><td><input id="uid" name="uid" type="text"/></td></tr>
    <tr><td>Password:</td><td><input id="pwd" name="pwd" type="password"/></td></tr>
  </table>
  <div>
    <input type="hidden" name="referer" value="<?cs var:referer ?>">
    <input type="submit" name="login" value="Login" />
  </div>
</form>

<script type="text/javascript">
  var uid = document.getElementById("uid");
  uid.focus();
  uid.select();
</script>

<?cs include:"footer.cs"?>
