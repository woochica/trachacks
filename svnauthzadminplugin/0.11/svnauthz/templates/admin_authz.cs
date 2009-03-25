<h2>Manage Subversion Access Rights</h2>


<?cs if editgroup.name ?>
<form id="addgroupmember" class="addnew" method="post">
 <input type="hidden" name="editgroup" value="<?cs var:editgroup.url ?>" />
 <fieldset>
  <?cs if addgroupmember.error ?>
  <div class="system-message"><p><?cs var:addgroupmember.error ?></p></div>
  <?cs /if ?>

  <legend>Add Group Member to <?cs var:editgroup.name ?></legend>
  <div class="field">
   <label>Subject: <?cs call:hdf_select(editgroup.candidates, "subject", "", 0) ?>
   </label>
  </div>
  <p class="help">Add a new subject to a Subversion group.</p>
  <div class="buttons">
   <input type="submit" name="addgroupmember" value=" Add ">
  </div>
 </fieldset>
</form>
<?cs /if ?>

<?cs if editpath.name ?>
<form id="addpathmember" class="addnew" method="post">
 <input type="hidden" name="editpath" value="<?cs var:editpath.url ?>" />
 <fieldset>
  <?cs if addpathmember.error ?>
  <div class="system-message"><p><?cs var:addpathmember.error ?></p></div>
  <?cs /if ?>

  <legend>Add Path Member to <?cs var:editpath.name ?></legend>
  <div class="field">
   <label>Subject: <?cs call:hdf_select(editpath.candidates, "subject", "", 0) ?>
   </label>
  </div>
  <div class="field">
   <label>Read: <input type="checkbox" name="addpathmember_acl" value="R"/>
   </label>
  </div>
  <div class="field">
   <label>Write: <input type="checkbox" name="addpathmember_acl" value="W"/>
   </label>
  </div>
  <p class="help">Add a new subject to a Path.</p>
  <div class="buttons">
   <input type="submit" name="addpathmember" value=" Add ">
  </div>
 </fieldset>
</form>
<?cs /if ?>



<form id="addgroup" class="addnew" method="post">
 <fieldset>
  <?cs if addgroup.error ?>
  <div class="system-message"><p><?cs var:addgroup.error ?></p></div>
  <?cs /if ?>

  <legend>Add Group:</legend>
  <div class="field">
   <label>Group name: <input type="text" name="groupname" class="textwidget" /></label>
  </div>
  <p class="help">Add a new Subversion group.</p>
  <div class="buttons">
   <input type="submit" name="addgroup" value=" Add ">
  </div>
 </fieldset>
</form>

<form id="addpath" class="addnew" method="post">
 <fieldset>
  <?cs if addpath.error ?>
  <div class="system-message"><p><?cs var:addpath.error ?></p></div>
  <?cs /if ?>

  <legend>Add Path:</legend>
  <div class="field">
   <label>Path: <input type="text" name="path" class="textwidget" /></label>
  </div>
  <?cs if addpath.repository ?>
  <div class="field">
   <label>Repository: <input type="text" name="repository" class="textwidget" /></label>
  </div>
  <?cs /if?>
  <p class="help">Add a new Subversion path.</p>
  <div class="buttons">
   <input type="submit" name="addpath" value=" Add ">
  </div>
 </fieldset>
</form>

<form method="post">
  <?cs if delgroup.error ?>
	<div class="system-message"><p><?cs var:delgroup.error ?></p></div>
  <?cs /if ?>
 <table class="listing" id="grouplist">
  <thead>
   <tr><th class="sel">&nbsp;</th><th>Subversion Groups</th></tr>
  </thead><tbody>
  <?cs each:group = groups ?>
   <tr>
    <td><input type="checkbox" name="selgroup" value="<?cs var:group.url ?>" /></td>
    <td><a href="<?cs var:group.href ?>"><?cs var:group.name ?></a>
	<?cs if editgroup.url == group.url ?>
		  <?cs if delgroupmember.error ?>
  			<div class="system-message"><p><?cs var:delgroupmember.error ?></p></div>
  		  <?cs /if ?>

  			<input type="hidden" name="editgroup" value="<?cs var:editgroup.url ?>" />
		<table class="listing" id="editgrouplist">
  			<thead>
   				<tr><th class="sel">&nbsp;</th><th>Group Members</th></tr>
  			</thead><tbody>			
  			<?cs each:groupmember = editgroup.members ?>
			<tr>
			<td><input type="checkbox" name="selgroupmember" value="<?cs var:groupmember ?>"/></td>
			<td><?cs var:groupmember ?></td>
			</tr>
			<?cs /each ?>
		</tbody></table>
		<div class="buttons">
  			<input type="submit" name="removegroupmembers" value="Remove selected group members" />
 		</div>
	<?cs /if ?>    
    </td>
   </tr>
  <?cs /each ?>
  </tbody>
 </table>
 <div class="buttons">
  <input type="submit" name="removegroups" value="Remove selected groups" />
 </div>
</form>

<form method="post">
  <?cs if delpath.error ?>
	<div class="system-message"><p><?cs var:delpath.error ?></p></div>
  <?cs /if ?>
 <table class="listing" id="pathlist">
  <thead>
   <tr><th class="sel">&nbsp;</th><th>Subversion Paths</th></tr>
  </thead><tbody><?cs
   each:path = paths ?>
   <tr>
    <td><input type="checkbox" name="selpath" value="<?cs var:path.url ?>" /></td>
    <td><a href="<?cs var:path.href ?>"><?cs var:path.name ?></a>
	<?cs if editpath.url == path.url ?>
		  <?cs if changepathmember.error ?>
  			<div class="system-message"><p><?cs var:changepathmember.error ?></p></div>
  		  <?cs /if ?>

  			<input type="hidden" name="editpath" value="<?cs var:editpath.url ?>" />
		<table class="listing" id="editpathlist">
  			<thead>
   				<tr><th class="sel">Remove</th><th>Path Members</th><th>Read</th><th>Write</th></tr>
  			</thead><tbody>			
  			<?cs each:pathmember = editpath.members ?>
			<tr>
			<td><input type="checkbox" name="selpathmember" value="<?cs var:pathmember.subject ?>"/></td>
			<td><?cs var:pathmember.subject ?></td>
			<td><input type="checkbox" name="selpathmember_acl" value="<?cs var:pathmember.subject ?>_R" <?cs var:pathmember.read ?> /></td>
			<td><input type="checkbox" name="selpathmember_acl" value="<?cs var:pathmember.subject ?>_W" <?cs var:pathmember.write ?> /></td>
			</tr>
			<?cs /each ?>
		</tbody></table>
		<div class="buttons">
  			<input type="submit" name="changepathmembers" value="Change path members" />
 		</div>
	<?cs /if ?>    
    </td>
   </tr><?cs
  /each ?></tbody>
 </table>
 <div class="buttons">
  <input type="submit" name="removepaths" value="Remove selected paths" />
 </div>
</form>

