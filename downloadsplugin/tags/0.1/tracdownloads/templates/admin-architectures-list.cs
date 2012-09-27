<?cs include "downloads-macros.cs" ?>

<h2>Architectures</h2>

<?cs if:downloads.architecture.id ?>
  <form id="edit-architecture-form" class="addnew" method="post" action="<?cs var:downloads.href ?>">
<?cs else ?>
  <form id="add-architecture-form" class="addnew" method="post" action="<?cs var:downloads.href ?>">
<?cs /if ?>
  <fieldset>
    <legend>
      <?cs if:downloads.architecture.id ?>
        Edit Architecture:
      <?cs else ?>
        Add Architecture:
      <?cs /if ?>
    </legend>

    <div class="field">
      <label for="name">Name:</label><br/>
      <input type="text" id="name" name="name" value="<?cs var:downloads.architecture.name ?>"/><br/>
    </div>

    <div class="field">
      <label for="description">Description:</label><br/>
      <input type="text" id="description" name="description" value="<?cs var:downloads.architecture.description ?>"/><br/>
    </div>

    <div class="buttons">
      <?cs if:downloads.architecture.id ?>
        <input type="submit" name="submit" value="Edit"/>
        <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:downloads.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>'"/>
        <input type="hidden" name="id" value="<?cs var:downloads.architecture.id ?>"/>
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

<?cs if:downloads.architectures.0.id ?>
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
        <?cs each:architecture = downloads.architectures ?>
          <tr class="<?cs if:architecture.id % #2 ?>odd<?cs else ?>even<?cs /if ?>">
            <td class="sel">
              <input type="checkbox" name="selection" value="<?cs var:architecture.id ?>"/>
            </td>

            <td class="id">
              <div class="id">
                <a href="<?cs var:downloads.href?>/<?cs var:architecture.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:architecture.id ?>
                </a>
              </div>
            </td>

            <td class="name">
              <div class="name">
                <a href="<?cs var:downloads.href ?>/<?cs var:architecture.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:architecture.name ?>
                </a>
              </div>
            </td>

            <td class="description">
              <div class="description">
                <a href="<?cs var:downloads.href ?>/<?cs var:architecture.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:architecture.description ?>
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
