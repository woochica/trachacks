<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>Contraseñas de LDAP</h1>

  <p>
 Esta página te permite cambiar la contraseña del LDAP. 
 Tener en cuenta que este cambio se realizará de forma <b>centralizada</b> y afectará a todos los 
 sistemas que utilizando el mismo LDAP, como por ejemplo el <b>Subversion</b>.
 </p>
 
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
   <label for="oldpassword" style="float:left;text-align:right;margin-top:5px;width:15em;">Contraseña antigua:</label>
   <input type="password" id="oldpassword" name="oldpassword" class="textwidget" size="30" />
  </div>
  &nbsp;
  &nbsp;
  <div>
   <label for="password1" style="float:left;text-align:right;margin-top:5px;width:15em;">Nueva contraseña:</label>
   <input type="password" id="password1" name="password1" class="textwidget" size="30" />
  </div>
  <div>
   <label for="password2" style="float:left;text-align:right;margin-top:5px;width:15em;">Confirmar contraseña:</label>
   <input type="password" id="password2" name="password2" class="textwidget" size="30" />
  </div>  
  <div>
  </fieldset>
   <br />
   <input type="submit" value="Actualizar contraseña" />
  </div >
 
</form>

<?cs include:"footer.cs"?>