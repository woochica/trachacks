<h2>E-Mail account information</h2>

<form id="config" class="addnew" method="post">
 <fieldset>
  <legend>Information Gathering</legend>
  <table>
    <?cs if:admin.ldap_import ?>
      <tr>
        <td><input type="checkbox" name="use_ldap" value="use_ldap" 
	  <?cs if:admin.options.use_ldap ?>checked="checked"<?cs /if?>/></td>
        <td><label>... from LDAP</label></td>
      </tr>
    <?cs /if?>
    <tr> 
     <td><input type="checkbox" name="use_file" value="use_file"
	<?cs if:admin.options.use_file ?>checked="checked"<?cs /if?>/></td>
     <td><label>... from file</label></td>
    </tr>
    <tr>
      <td><label>&nbsp;</label></td>
      <td><input type="text" name="filename" class="textwidget" 
		value="<?cs var:admin.options.filename ?>"/></td>
    </tr>
    <tr>
     <td><input type="checkbox" name="overwrite" value="overwrite"
	<?cs if:admin.options.overwrite ?>checked="checked"<?cs /if?>/></td>
     <td><label>overwrite information</label></td>
    </tr>
  </table>
  <div class="buttons">
   <input type="submit" name="fill" value=" Fill ">
  </div>
 </fieldset>
</form>

<form id="change" class="addnew" method="post">
 <fieldset>
  <legend>Add/Change Notice Info</legend>
  <div class="field">
   <label>Id: <input type="text" name="change_id" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Name: <input type="text" name="change_name" class="textwidget" /></label>
  </div>
  <div class="field">
   <label>Mail: <input type="text" name="change_mail" class="textwidget" /></label>
  </div>
  <p class="help">Add/Change the information.</p>
  <div class="buttons">
   <input type="submit" name="change" value=" Change ">
  </div>
 </fieldset>
</form>


<form id="form" method="post">
 <table class="listing" id="list">
  <thead>
   <tr><th colspan="4">Groups</th></tr>
   <tr><th class="sel">&nbsp;</th><th>Id</th><th>Name</th><th>E-Mail</th></tr>
  </thead><tbody><?cs
  each:group = admin.groupinfos ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:group.id ?>" /></td>
    <td><?cs var:group.id ?></td>
    <td><?cs var:group.name ?></td>
    <td><?cs var:group.email ?></td>
   </tr><?cs
  /each ?></tbody>
  <thead>
    <tr><th colspan="4">Users</th></tr>
  </thead>
  <tbody><?cs
  each:user = admin.userinfos ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:user.id ?>" /></td>
    <td><?cs var:user.id ?></td>
    <td><?cs var:user.name ?></td>
    <td><?cs var:user.email ?></td>
   </tr><?cs
  /each ?></tbody>
 </table>
 <div class="buttons">
  <input type="submit" name="rminfo" value="Remove informations" />
  <input type="submit" name="rmuser" value="Remove user" />
  <input type="submit" name="rmall" value="Remove all" />
  <input type="submit" name="extract" value="Extract groups" />
 </div>
</form>

<?cs if:admin.error_message ?>
 <hr>
 <p><i>Notice</i></br>
 <?cs var:admin.error_message ?>
 </p>
<?cs /if?>
