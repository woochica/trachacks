<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<style type="text/css">
 input.openid_login {
   background: url(http://openid.net/login-bg.gif) no-repeat;
   background-color: #fff;
   background-position: 0 50%;
   color: #000;
   padding-left: 18px;
 }
 .message {color: red; font-weight: bold;}
</style>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="login">

<h2>Login</h2><?cs
  if:auth.message ?><p class="message"><?cs
    var:auth.message ?></p><?cs
  /if ?>

<form action="<?cs var:auth.handler ?>" method="post">
  <table border="0">
  <tr>
    <td><label for="openid_url">OpenID:</label></td>
    <td><input class="openid_login" size="30" id="openid_url" name="openid_url" type="text" /></td>
    <td><input type="submit" name="login" value="Login" /></td>
  </tr>
  </table>
</form>
</div>

<script type="text/javascript">
 var login = document.getElementById("openid_url");
 login.focus();
 login.select();
</script>

<?cs include:"footer.cs"?>
