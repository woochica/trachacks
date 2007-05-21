<h2>Manage Custom Fields</h2><?cs

if:admin.customfield.name ?>
 <form class="mod" id="addcf" method="post">
  <fieldset>
   <legend>Modify Custom Field:</legend>
   <div class="field">
    <label>Name (can not modify): <strong><?cs
      var:admin.customfield.name ?></strong></label>
   </div>
   <input name="name" value="<?cs var:admin.customfield.name ?>" type="hidden" />
   <input name="order" value="<?cs var:admin.customfield.order ?>" type="hidden" />
   <div class="field">
    <label>Type:<br /><select name="type" id="type">
    <option value="text"<?cs
       if:admin.customfield.type == "text" ?> selected="selected"<?cs
       /if ?>>Text</option>
    <option value="select"<?cs
       if:admin.customfield.type == "select" ?> selected="selected"<?cs
       /if ?>>Select</option>
    <option value="checkbox"<?cs
       if:admin.customfield.type == "checkbox" ?> selected="selected"<?cs
       /if ?>>Checkbox</option>
    <option value="radio"<?cs
       if:admin.customfield.type == "radio" ?> selected="selected"<?cs
       /if ?>>Radio</option>
    <option value="textarea"<?cs
       if:admin.customfield.type == "textarea" ?> selected="selected"<?cs
       /if ?>>Textarea</option>
    </select>
    </label>
   </div>
   <div class="field">
    <label>Label:<br /> <input type="text" name="label" value="<?cs
      var:admin.customfield.label ?>" /></label>
   </div>
   <div class="field">
    <label>Default value (regular text for Text/Textarea, or index number for Select):<br />
    <input type="text" name="value" value="<?cs
      var:admin.customfield.value ?>" /></label>
   </div>
   <div class="field">
    <fieldset class="iefix">
     <label for="options">Options for Radio or Select (for Select, empty first line makes field optional):</label>
     <p><textarea id="options" name="options" rows="5" cols="30">
<?cs var:admin.customfield.options ?></textarea>
    </fieldset>
   </div>
   <div class="field">
    <label for="cols">Size of Textarea for entry (Textarea only):<br />
      Columns: <input type="text" name="cols" id="cols" size="5" value="<?cs
      var:admin.customfield.width ?>" /> Rows: <input type="text" size="5" name="rows" id="rows" value="<?cs
      var:admin.customfield.height ?>" /></label>
   </div>
   <div class="buttons">
    <input type="submit" name="cancel" value="Cancel" />
    <input type="submit" name="save" value="Save" />
   </div>
  </fieldset>
 </form><?cs

else ?>

 <form class="addnew" id="addcf" method="post">
  <fieldset>
   <legend>Add Custom Field:</legend>
   <div class="field">
    <label>Name:<br /><input type="text" name="name" id="name" /></label>
   <div class="field">
    <label>Type:<br /><select name="type" id="type">
    <option value="text">Text</option>
    <option value="select">Select</option>
    <option value="checkbox">Checkbox</option>
    <option value="radio">Radio</option>
    <option value="textarea">Textarea</option>
    </select>
    </label>
   </div>
   <div class="field">
    <label>Label:<br /><input type="text" name="label" id="label" /></label>
   </div>
   <div class="field">
    <label for="value">Default value:<br /> <input type="text" name="value" id="value" /></label>
   </div>
   <div class="field">
    <fieldset class="iefix">
     <label for="options">Options:</label>
     <p><textarea id="options" name="options" rows="4" cols="17"></textarea>
    </fieldset>
   </div>
   <div class="field">
    <label for="cols">Size of Textarea:<br />
      Cols: <input type="text" name="cols" id="cols" size="2" />
      Rows: <input type="text" size="2" name="rows" id="rows" /></label>
   </div>
   <div class="buttons">
    <input type="submit" name="add" value="Add">
   </div>
  </fieldset>
 </form><?cs

 if:len(admin.customfields) ?><form method="POST">
  <table class="listing" id="cflist">
   <thead>
    <tr><th class="sel">&nbsp;</th><th>Name</th>
    <th>Type</th><th>Label</th><th>Order</th></tr>
   </thead><tbody><?cs
   each:cf = admin.customfields ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:cf.name ?>" /></td>
    <td><a href="<?cs var:cf.href ?>"><?cs var:cf.name ?></a></td>
    <td><?cs var:cf.type ?></td>
    <td><?cs var:cf.label ?></td>
    <td class="default"><select name="order_<?cs var:cf.name ?>"><?cs
	  each:other = admin.customfields ?><option<?cs
  	 if:other.order == cf.order ?> selected="selected"<?cs
  	 /if ?>><?cs var:other.order ?></option><?cs
  	/each ?>
 	</select></td>
   </tr><?cs
   /each ?></tbody>
  </table>
  <div class="buttons">
   <input type="submit" name="remove" value="Remove selected items" />
   <input type="submit" name="apply" value="Apply changes" />
  </div>
 </form><?cs
 else ?>
  <p class="help">No Custom Fields defined for this project.</p><?cs
 /if ?><?cs
 
/if ?>
