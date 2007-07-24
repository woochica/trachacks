<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="listing addSuite">
<h1><?cs var:manualtesting.suite.title ?></h1>

<?cs if:args.preview ?>
  <div class="message-list">
    <div class="topic">
      <div class="header">
        <div class="subject">
          <?cs var:discussion.subject ?>
        </div>
        <div class="body">
          <?cs var:discussion.body ?>
        </div>
        <div class="footer">
          <div class="author">
            <?cs var:discussion.author ?>
          </div>
          <div class="time">
            <?cs var:discussion.time ?>
          </div>
        </div>
      </div>
    </div>
  </div>
<?cs /if ?>

<form class="add_form" method="post" action="<?cs var:manualtesting.href ?>/<?cs var:manualtesting.suite.id ?>">
    <fieldset>
        <legend>Add Test Plan:</legend>
        <div class="field">
            <label for="user">Your email or username:</label><br/>
            <input type="text" name="user" size="40" value="<?cs alt:trac.authname ?>anonymous<?cs /alt ?>" /><br/>
        </div>
        <div class="field">
            <label for="priority">Priority:</label><br/>
            <select name="priority">
                <?cs each:priority = manualtesting.trac.priorities ?>
                    <?cs if $priority.name == 'major' ?>
                        <option selected="selected">
                    <?cs else ?>
                        <option>
                    <?cs /if ?>
                            <?cs var:priority.name ?>
                        </option>
                <?cs /each ?>
            </select><br/>
        </div>
        <div class="field">
            <label for="title">Title:</label><br/>
            <input type="text" name="title" size="80" value="<?cs var:args.subject ?>" /><br/>
        </div>
        <div class="field">
            <label for="description">Description:</label><br/>
            <textarea name="description" class="wikitext" rows="10" cols="78"><?cs alt:args.body ?><?cs /alt ?></textarea><br/>
        </div>
        <div class="buttons">
            <!-- <input type="submit" name="preview" value="Preview" /> -->
            <input type="submit" name="submit" value="Submit" />
            <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:discussion.href?>/<?cs var:discussion.forum.id ?>'"/>
            <input type="hidden" name="manualtesting_action" value="plan-add" />
        </div>
    </fieldset>
</form>

<?cs include "discussion-footer.cs" ?>