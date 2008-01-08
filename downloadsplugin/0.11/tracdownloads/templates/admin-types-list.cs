<?cs include "downloads-macros.cs" ?>

<h2>Types</h2>

<?cs if:downloads.type.id ?>
  <form id="edit-type-form" class="addnew" method="post" action="<?cs var:downloads.href ?>">
<?cs else?>
  <form id="add-type-form" class="addnew" method="post" action="<?cs var:downloads.href ?>">
<?cs /if ?>
  <fieldset>
    <legend>
      <?cs if:downloads.type.id ?>
        Edit Type:
      <?cs else ?>
        Add Type:
      <?cs /if ?>
    </legend>

    <div class="field">
      <label for="name">Name:</label><br/>
      <input type="text" id="name" name="name" value="<?cs var:downloads.type.name ?>"/><br/>
    </div>

    <div class="field">
      <label for="description">Description:</label><br/>
      <input type="text" id="description" name="description" value="<?cs var:downloads.type.description ?>"/><br/>
    </div>

    <div class="buttons">
      <?cs if:downloads.type.id ?>
        <input type="submit" name="submit" value="Edit"/>
        <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:downloads.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>'"/>
        <input type="hidden" name="id" value="<?cs var:downloads.type.id ?>"/>
        <input type="hidden" name="action" value="post-edit"/>
      <?cs else ?>
        <input type="submit" name="submit" value="Add"/>
        <input type="hidden" name="action" value="post-add"/>
      <?cs /if ?>
      <input type="hidden" name="order" value="<?cs var:downloads.order ?>"/>
      <input type="hidden" name="desc" value="<?cs var:downloads.desc ?>"/>
    </div>
  </fieldset>
</form>

<?cs if:downloads.types.0.id ?>
  <form method="post" action="<?cs var:discussion.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
    <table class="listing">
      <thead>
        <tr>
          <th class="sel">&nbsp;</th>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'id', 'ID', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'name', 'Name', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'description', 'Description', downloads.href) ?>
        </tr>
      </thead>
      <tbody>
        <?cs each:type = downloads.types ?>
          <tr class="<?cs if:type.id % #2 ?>odd<?cs else ?>even<?cs /if ?>">
            <td class="sel">
              <input type="checkbox" name="selection" value="<?cs var:type.id ?>"/>
            </td>

            <td class="id">
              <div class="id">
                <a href="<?cs var:downloads.href?>/<?cs var:type.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:type.id ?>
                </a>
              </div>
            </td>

            <td class="name">
              <div class="name">
                <a href="<?cs var:downloads.href ?>/<?cs var:type.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:type.name ?>
                </a>
              </div>
            </td>

            <td class="description">
              <div class="description">
                <a href="<?cs var:downloads.href ?>/<?cs var:type.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:type.description ?>
                </a>
              </div>
            </td>
          </tr>
        <?cs /each ?>
      </tbody>
    </table>

    <div class="buttons">
      <input type="submit" name="remove" value="Remove selected items" />
      <input type="hidden" name="action" value="delete"/>
    </div>
  </form>
<?cs else ?>
  <p class="help">As long as you don't add any items to the list, this field
    will remain completely hidden from the user interface.</p>
  <br style="clear: right"/>
<?cs /if ?>
