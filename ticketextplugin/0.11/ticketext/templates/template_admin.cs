<h2>Manage Ticket Template</h2>

<form class="mod" id="modtemplate" method="post">
  <fieldset>
    <legend>Change the ticket template</legend>
    <div class="field">
      <label for="type">Ticket Type:</label><br />
      <select id="type" name="type">
        <?cs each:type = ticketext.template.types ?>
        <option value="<?cs var:type.name ?>" <?cs if:type.selected ?>selected="selected"<?cs /if ?>>
          <?cs var:type.name ?>
        </option>
        <?cs /each ?>
      </select>
    </div>
    <div class="field">
      <label for="template">Ticket Description(you may use <a tabindex="42" href="<?cs var:$trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label><br />
      <textarea id="template" name="template" class="wikitext" rows="10" cols="78" style="{width : 98%}"><?cs var:ticketext.template.template ?></textarea>
    </div>
  </fieldset>
  
  <br />
  
  <fieldset>
    <legend>Enable custom fields</legend>
    <?cs if:len(ticketext.template.customfields) ?>
    <table id="cflist" class="listing">
      <thead>
        <tr>
          <th class="sel">&nbsp;</th>
          <th>Name</th>
          <th>Type</th>
          <th>Label</th>
        </tr>
      </thead>
      <tbody>
        <?cs each:cf = ticketext.template.customfields ?>
        <tr>
          <td><input type="checkbox" name="cf-enable" value="<?cs var:cf.name ?>"
              <?cs if:cf.enable == 1 ?>checked="checked"<?cs /if ?> /></td>
          <td><?cs var:cf.name ?></td>
          <td><?cs var:cf.type ?></td>
          <td><?cs var:cf.label ?></td>
        </tr>
        <?cs /each ?>
      </tbody>
    </table>
    <?cs else ?>
      <p class="help">No Custom Fields defined for this project.</p>
    <?cs /if ?>    
  </fieldset>
  
  <script type="text/javascript" src="<?cs var:htdocs_location ?>js/wikitoolbar.js"></script>
  
  <div class="buttons">
    <input type="submit" value="Apply changes">
  </div>
</form>
