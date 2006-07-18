<h2>Project Settings</h2><?cs

if:projmanager.saved_message ?>
  <p class="saved_message"><?cs
      var:projmanager.saved_message ?>
  </p><?cs
/if ?>

<form class="mod" id="modbasic" method="post">
 <fieldset>
  <legend>Project</legend>
  <div class="field">
   <label>Name:<br />
    <input type="text" name="name" value="<?cs var:projmanager.project.name ?>" readonly="true"/>
   </label>
  </div>
  <div class="field">
   <label>Description:<br />
    <textarea name="description" rows="3" cols="80"><?cs
      var:projmanager.project.description ?></textarea>
   </label>
  </div>
 </fieldset>
 <div class="buttons">
  <input type="submit" value="Apply changes">
 </div>
</form>
