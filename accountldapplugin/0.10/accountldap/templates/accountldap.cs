<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>Change your LDAP password</h1>

  <p>This page let you change your LDAP password. If you happen to use LDAP as centrlize authentication for other system such as Subversion, this will also change every passwords associate with LDAP server</p>
 
 <?cs if:accountldap.message != None ?>
 <fieldset>
 <legend>Aviso</legend>
 <?cs var:accountldap.message ?>
  </fieldset>
  <?cs /if ?>
&nbsp;
 <form method="post" action="">
 <fieldset>
 <legend>Cambio de contraseña</legend>
  <div>
   <label for="oldpassword" style="float:left;text-align:right;margin-top:5px;width:15em;">Old password: </label>
   <input type="password" id="oldpassword" name="oldpassword" class="textwidget" size="30" />
  </div>
  &nbsp;
  &nbsp;
  <div>
   <label for="password1" style="float:left;text-align:right;margin-top:5px;width:15em;">New password: </label>
   <input type="password" id="password1" name="password1" class="textwidget" size="30" />
  </div>
  <div>
   <label for="password2" style="float:left;text-align:right;margin-top:5px;width:15em;">Confirm password: </label>
   <input type="password" id="password2" name="password2" class="textwidget" size="30" />
  </div>  
  <div>
  </fieldset>
   <br />
   <input type="submit" value="Actualizar contraseña" />
  </div >
 
</form>

<?cs include:"footer.cs"?>
