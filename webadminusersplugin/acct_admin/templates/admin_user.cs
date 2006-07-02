<h2>Change Password</h2>

<?cs if users.error ?>
 <div class="system-message">
  <?cs var:users.error ?>
 </div>
<?cs /if ?>

<form class="mod" id="usermod" method="post">
  <fieldset>
    <legend>Change Password:</legend>
    <div class="field">
      <label>Name: <?cs var:admin.user ?> </label>
    </div>
    <div class="field">
      <label>Password: <input type="password" name="password1" /></label>
    </div>
    <div class="field">
      <label>Confirm Password: 
      <input type="password" name="password2" /></label>
    </div>
    <div class="buttons">
      <input type="submit" name="change" value=" Change Password "/>
      <input type="submit" name="delete" value=" Delete Account "/>
      <input type="submit" name="cancel" value=" Cancel "/>
    </div>
  </fieldset>
</form>
