<h2>Forum Groups</h2>

<form class="addnew" method="post">
  <fieldset>
    <legend>
       Add Forum Group:
    </legend>
    <div class="field">
      <label for="name">Name:</label><br/>
      <input type="text" name="name" value=""/><br/>
    </div>
    <div class="field">
      <label for="description">Description:</label><br/>
      <input type="text" name="description" value=""/><br/>
    </div>
    <div class="buttons">
      <input type="submit" name="submit" value="Add"/>
      <input type="hidden" name="discussion_action" value="post-add"/>
    </div>
  </fieldset>
</form>

<?cs if:discussion.groups.1.id ?>
  <form class="forum-list" method="post">
    <table class="listing">
      <thead>
        <tr>
          <th class="selection">&nbsp;</th>
          <th class="name">Name</th>
          <th class="description">Description</th>
        </tr>
      </thead>
      </tbody>
        <?cs each:group = discussion.groups ?>
          <?cs if:group.id ?>
            <tr class="<?cs if:name(group) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
              <td class="selection">
                <input type="checkbox" name="selection" value="<?cs var:group.id ?>"/>
              </td>
              <td class="name">
                <div class="name"><?cs var:group.name ?></div>
              </td>
              <td class="description">
                <div class="description" ><?cs var:group.description ?></div>
              </td>
            </tr>
          <?cs /if ?>
        <?cs /each ?>
      </tbody>
    </table>
    <div class="buttons">
      <input type="submit" name="remove" value="Remove selected items" />
      <input type="hidden" name="discussion_action" value="delete"/>
    </div>
  </form>
<?cs else ?>
  <p class="help">As long as you don't add any items to the list, this field
  will remain completely hidden from the user interface.</p>
  <br style="clear: right"/>
<?cs /if ?>
