<?cs include "discussion-header.cs" ?>

<h1>Add Forum</h1>
<form class="add_form" method="post" action="<?cs var:trac.href.discussion ?>">
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
      <?cs if:discussion.users ?>
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
      <input type="submit" name="submit" value="Submit"/>
      <input type="submit" name="cancel" value="Cancel"/>
      <input type="hidden" name="action" value="post-add"/>
    </div>
  </fieldset>
</form>

<?cs include "discussion-footer.cs" ?>