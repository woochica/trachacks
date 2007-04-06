<h2>Values for <?cs var:hidevals.field.label ?></h2>

<form id="addhideval" class="addnew" method="post">
  <fieldset>
    <legend>Add Field Mask</legend>
    <div class="field">
      <label>Group: <br />
        <input type="text" name="group" />
      </label>
    </div>
    <div class="field">
      <label>Value: <br />
        <select name="value">
          <?cs each:opt = hidevals.field.options ?>
            <option value="<?cs var:opt ?>"><?cs var:opt ?></option>
          <?cs /each ?>
        </select>
      </label>
    </div>
    <p class="help">Allow a group to see the given field value</p>
    <div class="buttons">
      <input type="submit" name="add" value="Add" />
    </div>
  </fieldset>
</form>
    
<form id="enablehideval" method="post">
  Filtering for this field is currently <?cs if:hidevals.enabled ?>enabled<?cs else ?>disabled<?cs /if ?>.
  <input type="submit" name="toggle" value="<?cs if:hidevals.enabled ?>Disable<?cs else ?>Enable<?cs /if ?>">
</form>
    
<form id="listhideval" method="post">
  <table class="listing">
    <thead>
      <tr>
        <th class="sel">&nbsp;</th>
        <th>Group</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      <?cs each:val = hidevals.values ?>
        <tr>
          <td><input type="checkbox" name="sel" value="<?cs var:val.group ?>#<?cs var:val.value ?>" /></td>
          <td><?cs var:val.group ?></td>
          <td><?cs var:val.value ?></td>
        </tr>
      <?cs /each ?>
    </tbody>
  </table>
  <div class="buttons">
     <input type="submit" name="remove" value="Remove selected items" />
  </div>
</form>
