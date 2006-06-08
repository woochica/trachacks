<script type="text/javascript">
  function submit_group_change(forum)
  {
    var forum_list_form = document.getElementById('forum-list-form');
    var group_select = document.getElementById('group-select-' + forum);
    forum_list_form.action.value = 'change-group';
    forum_list_form.group.value = group_select.value;
    forum_list_form.forum.value = forum;
    forum_list_form.submit();
  }
</script>

<h2>Forums</h2>

<form class="addnew" method="post">
  <fieldset>
    <legend>
       Add Forum:
    </legend>
    <div class="field">
      <label for="name">Name:</label><br/>
      <input type="text" name="name" value=""/><br/>
    </div>
    <div class="field">
      <label for="subject">Subject:</label><br/>
      <input type="text" name="subject" value=""/><br/>
    </div>
    <div class="field">
      <label for="description">Description:</label><br/>
      <input type="text" name="description" value=""/><br/>
    </div>
    <div class="field">
      <label for="moderators">Moderators:</label><br/>
      <?cs if:discussion.users.0 ?>
        <select name="moderators" multiple="on">
          <?cs each:user = discussion.users ?>
            <option value="<?cs var:user ?>"><?cs var:user ?></option>
          <?cs /each ?>
        </select><br/>
      <?cs else ?>
        <input type="text" name="moderators" value=""/><br/>
      <?cs /if ?>
    </div>
    <div class="buttons">
      <input type="submit" name="submit" value="Add"/>
      <input type="hidden" name="action" value="post-add"/>
    </div>
  </fieldset>
</form>

<?cs if:discussion.forums.0.id ?>
  <form id="forum-list-form" class="forum-list" method="post">
    <table class="listing">
      <thead>
        <tr>
          <th class="selection">&nbsp;</th>
          <th class="name">Name</th>
          <th class="subject">Subject</th>
          <th class="description">Description</th>
          <th class="moderators">Moderators</th>
          <?cs if:discussion.groups.0.id ?>
            <th class="group">Group</th>
          <?cs /if ?>
        </tr>
      </thead>
      </tbody>
        <?cs each:forum = discussion.forums ?>
          <tr class="<?cs if:name(forum) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
            <td class="selection">
              <input type="checkbox" name="selection" value="<?cs var:forum.id ?>"/>
            </td>
            <td class="name">
              <div class="name"><?cs var:forum.name ?></div>
            </td>
            <td class="subject">
              <div class="subject"><?cs var:forum.subject ?></div>
            </td>
            <td class="description">
              <div class="description"><?cs var:forum.description ?></div>
            </td>
            <td class="moderators">
              <div class="moderators"><?cs var:forum.moderators ?></div>
            </td>
            <?cs if:discussion.groups.0.id ?>
              <td class="group">
                <div class="group">
                  <select id="group-select-<?cs var:forum.id ?>" name="group-<?cs var:forum.id ?>" onChange="submit_group_change(<?cs var:forum.id ?>)">
                    <option value="">None</option>
                    <?cs each:group = discussion.groups ?>
                      <?cs if:group.id == forum.group ?>
                        <option value="<?cs var:group.id ?>" selected="selected"><?cs var:group.name ?></option>
                      <?cs else ?>
                        <option value="<?cs var:group.id ?>"><?cs var:group.name ?></option>
                      <?cs /if ?>
                    <?cs /each ?>
                  </select>
                </div>
              </td>
            <?cs /if ?>
          </tr>
        <?cs /each ?>
      </tbody>
    </table>
    <div class="buttons">
      <input type="submit" name="remove" value="Remove selected items" />
      <input type="hidden" name="action" value="delete"/>
      <input type="hidden" name="group" value=""/>
      <input type="hidden" name="forum" value=""/>
    </div>
  </form>
<?cs else ?>
  <p class="help">As long as you don't add any items to the list, this field
  will remain completely hidden from the user interface.</p>
  <br style="clear: right"/>
<?cs /if ?>
