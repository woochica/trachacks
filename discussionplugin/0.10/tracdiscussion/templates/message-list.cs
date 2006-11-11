<?cs def:display_preview() ?>
  <li class="preview">
    <a name="preview"></a>
    <div class="id">
        Message #??
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
  </li>
<?cs /def ?>

<?cs def:display_reply_form() ?>
  <li class="reply">
    <fieldset>
      <a name="reply"></a>
      <legend>
         Reply:
      </legend>
      <form method="post" action="<?cs var:discussion.href ?>#preview">
        <div class="field">
          <label for="author">Author:</label><br/>
          <?cs if:args.author ?>
            <input type="text" id="author" name="author" value="<?cs var:args.author ?>"/><br/>
          <?cs else ?>
            <input type="text" id="author" name="author" value="<?cs var:discussion.authname ?>"/><br/>
          <?cs /if ?>
        </div>
        <div class="field">
          <label for="body">Body:</label><br/>
          <textarea id="body" name="body" class="wikitext" rows="10" cols="78"><?cs alt:args.body ?>Enter your message here...<?cs /alt ?></textarea>
        </div>
        <div class="buttons">
          <input type="submit" name="preview" value="Preview"/>
          <input type="submit" name="submit" value="Reply"/>
          <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:discussion.href ?>#<?cs var:args.message ?>'"/>
        </div>
        <?cs if:args.message ?>
          <input type="hidden" name="message" value="<?cs var:args.message ?>"/>
        <?cs /if ?>
        <input type="hidden" name="redirect" value="1"/>
        <input type="hidden" name="discussion_action" value="post-add"/>
      </form>
    </fieldset>
  </li>
<?cs /def ?>

<?cs def:display_edit_form() ?>
  <fieldset>
    <a name="reply"></a>
    <legend>
      Edit:
    </legend>
    <form method="post" action="<?cs var:discussion.href ?>#preview">
      <?cs if:!args.message ?>
        <div class="field">
          <label for="subject">Subject:</label><br/>
          <input type="text" id="subject" name="subject" value="<?cs var:args.subject ?>"/><br/>
        </div>
      <?cs /if ?>
      <div class="field">
        <label for="body">Body:</label><br/>
        <textarea id="body" name="body" class="wikitext" rows="10" cols="78"><?cs var:args.body ?></textarea>
      </div>
      <div class="buttons">
        <input type="submit" name="preview" value="Preview"/>
        <input type="submit" name="submit" value="Submit changes"/>
        <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:discussion.href ?>#<?cs var:args.message ?>'"/>
      </div>
      <?cs if:args.message ?>
        <input type="hidden" name="message" value="<?cs var:args.message ?>"/>
      <?cs /if ?>
      <input type="hidden" name="redirect" value="1"/>
      <input type="hidden" name="discussion_action" value="post-edit"/>
    </form>
  </fieldset>
<?cs /def ?>

<?cs def:display_set_display() ?>
  <div class="set-display">
    <a href="<?cs var:discussion.href ?>?discussion_action=set-display;display=tree">Tree View</a>
    <a href="<?cs var:discussion.href ?>?discussion_action=set-display;display=flat-desc">Flat View (newer first)</a>
    <a href="<?cs var:discussion.href ?>?discussion_action=set-display;display=flat-asc">Flat View (older first)</a>
  </div>
<?cs /def ?>

<?cs def:display_topic(messages) ?>
  <?cs each:message = messages ?>
    <li <?cs if:message.new ?>class="new"<?cs /if ?>>
      <a name="<?cs var:message.id ?>"></a>
      <div class="id">
        Message #<?cs var:message.id ?>
      </div>
      <div class="body">
        <?cs if:(args.message == message.id) && args.preview ?>
          <?cs var:discussion.body ?>
        <?cs else?>
          <?cs var:message.body ?>
        <?cs /if ?>
      </div>
      <div class="controls">
        <?cs if:trac.acl.DISCUSSION_APPEND ?>
          <a href="<?cs var:discussion.href ?>?discussion_action=add;message=<?cs var:message.id ?>#reply">Reply</a>
          <a href="<?cs var:discussion.href ?>?discussion_action=quote;message=<?cs var:message.id ?>#reply">Quote</a>
          <?cs if:discussion.is_moderator || ((message.author == discussion.authname) && (discussion.authname != 'anonymous')) ?>
            <a href="<?cs var:discussion.href ?>?discussion_action=edit;message=<?cs var:message.id ?>#reply">Edit</a>
          <?cs /if ?>
        <?cs /if ?>
        <?cs if:trac.acl.DISCUSSION_MODERATE && discussion.is_moderator ?>
          <a href="<?cs var:discussion.href ?>?discussion_action=delete;message=<?cs var:message.id ?>" onclick="return confirm('Do you realy want to delete this reply and all its descendants?')"/>Delete</a>
        <?cs /if ?>
      </div>
      <div class="footer">
        <div class="author">
          <?cs var:message.author ?>
        </div>
        <div class="time">
          <?cs var:message.time ?>
        </div>
      </div>
      <?cs if:(args.message == message.id) && !args.submit && ((args.discussion_action == 'edit') || (args.discussion_action == 'post-edit')) ?>
        <?cs call:display_edit_form() ?>
      <?cs /if ?>
    </li>
    <?cs if:message.replies.0.id || args.discussion_action && ((args.discussion_action == 'add') || (args.discussion_action == 'quote') || (args.discussion_action == 'post-add')) ?>
      <ul class="reply">
        <?cs if:message.replies.0.id ?>
          <?cs call:display_topic(message.replies) ?>
        <?cs /if ?>
        <?cs if:(args.message == message.id) && !args.submit && (args.discussion_action && (args.discussion_action == 'add') || (args.discussion_action == 'quote') || (args.discussion_action == 'post-add')) ?>
          <?cs if:args.preview ?>
            <?cs call:display_preview() ?>
          <?cs /if ?>
          <?cs call:display_reply_form() ?>
        <?cs /if ?>
      </ul>
    <?cs /if ?>
  <?cs /each ?>
<?cs /def ?>

<?cs if:discussion.no_navigation ?>
  <div id="message-list" class="message-list">
  <h2>Discussion</h2>
<?cs else ?>
  <?cs linclude "discussion-header.cs" ?>
  <h1>Forum #<?cs var:discussion.forum.id ?> - Topic #<?cs var:discussion.topic.id ?> - Message List</h1>
<?cs /if?>

<?cs if:discussion.component != 'wiki' ?>
  <?cs set:discussion.href = discussion.href + '/' + discussion.forum.id + '/' + discussion.topic.id ?>
<?cs /if ?>

<?cs if:trac.acl.DISCUSSION_VIEW ?>
  <?cs if:!discussion.no_display && discussion.topic.id ?>
    <a name="-1"></a>
    <div class="topic <?cs if:discussion.topic.new ?>new<?cs /if ?>">
      <div class="header">
        <div class="subject">
          <?cs if:!args.message && args.preview ?>
            <?cs var:discussion.subject ?>
          <?cs else?>
            <?cs var:discussion.topic.subject ?>
          <?cs /if ?>
        </div>
      </div>
      <div class="body">
        <?cs if:!args.message && args.preview ?>
          <?cs var:discussion.body ?>
        <?cs else?>
          <?cs var:discussion.topic.body ?>
        <?cs /if ?>
      </div>
      <div class="controls">
        <?cs if:trac.acl.DISCUSSION_APPEND ?>
          <a href="<?cs var:discussion.href ?>?discussion_action=add;#reply">Reply</a>
          <a href="<?cs var:discussion.href ?>?discussion_action=quote;#reply">Quote</a>
          <?cs if:discussion.is_moderator || ((discussion.topic.author == discussion.authname) && (discussion.authname != 'anonymous'))?>
            <a href="<?cs var:discussion.href ?>?discussion_action=edit;#reply">Edit</a>
          <?cs /if ?>
        <?cs /if ?>
      </div>
      <div class="footer">
        <div class="author">
          <?cs var:discussion.topic.author ?>
        </div>
        <div class="time">
          <?cs var:discussion.topic.time ?>
        </div>
      </div>
      <?cs if:!args.message && !args.submit && ((args.discussion_action == 'edit') || (args.discussion_action == 'post-edit')) ?>
        <?cs call:display_edit_form() ?>
      <?cs /if ?>
    </div>
    <?cs if:discussion.messages.0.id || args.discussion_action && ((args.discussion_action == 'add') || (args.discussion_action == 'quote') || (args.discussion_action == 'post-add')) ?>
      <div class="replies <?cs if:discussion.topic.new ?>new<?cs /if ?>">
        <?cs call:display_set_display() ?>
        <ul class="reply">
          <?cs if:discussion.messages.0.id ?>
            <?cs call:display_topic(discussion.messages) ?>
          <?cs /if ?>
          <?cs if:!args.message && !args.submit && args.discussion_action && ((args.discussion_action == 'add') || (args.discussion_action == 'quote') || (args.discussion_action == 'post-add')) ?>
            <?cs if:args.preview ?>
              <?cs call:display_preview() ?>
            <?cs /if ?>
            <?cs call:display_reply_form() ?>
          <?cs /if ?>
        </ul>
        <?cs call:display_set_display() ?>
      </div>
    <?cs /if ?>
  <?cs else?>
    <span>No discussion for this page created.</span>
  <?cs /if ?>
<?cs else ?>
  <span>You have no rights to see this discussion.</span>
<?cs /if ?>

<?cs if:trac.acl.DISCUSSION_MODERATE && discussion.is_moderator ?>
  <div class="buttons">
    <form method="post" action="<?cs var:discussion.href ?>">
      <input type="submit" name="deletetopic" value="Delete Topic" onclick="return confirm('Do you realy want to delete this topic?')"/>
      <input type="hidden" name="discussion_action" value="delete"/>
    </form>
    <?cs if:!discussion.no_navigation ?>
      <form method="post" action="<?cs var:discussion.href ?>">
        <input type="submit" name="movetopic" value="Move Topic"/>
        <input type="hidden" name="discussion_action" value="move"/>
      </form>
    <?cs /if ?>
  </div>
<?cs /if ?>

<?cs if:discussion.no_navigation ?>
  </div>
<?cs else ?>
  <?cs linclude "discussion-footer.cs" ?>
<?cs /if?>


