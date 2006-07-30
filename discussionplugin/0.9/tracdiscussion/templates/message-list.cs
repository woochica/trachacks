<?cs def:display_preview() ?>
  <li class="preview">
    <a name="preview"></a>
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

<?cs def:display_form() ?>
  <li class="reply">
    <fieldset>
      <a name="reply"></a>
      <legend>
         Reply:
      </legend>
      <form method="get" action="<?cs var:discussion.href ?>#preview">
        <div class="field">
          <label for="author">Author:</label><br/>
          <?cs if:args.author ?>
            <input type="text" name="author" value="<?cs var:args.author ?>"/><br/>
          <?cs else ?>
            <input type="text" name="author" value="<?cs var:discussion.authname ?>"/><br/>
          <?cs /if ?>
        </div>
        <div class="field">
          <label for="body">Body:</label><br/>
          <textarea name="body" class="wikitext" rows="10" cols="78"><?cs alt:args.body ?>Enter your message here...<?cs /alt ?></textarea>
        </div>
        <div class="buttons">
          <input type="submit" name="preview" value="Preview"/>
          <input type="submit" name="submit" value="Reply"/>
          <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:discussion.href ?>#<?cs var:args.message ?>'"/>
        </div>
        <?cs if:args.message ?>
          <input type="hidden" name="message" value="<?cs var:args.message ?>"/>
        <?cs /if ?>
        <input type="hidden" name="discussion_action" value="post-add"/>
      </form>
    </fieldset>
  </li>
<?cs /def ?>

<?cs def:display_topic(messages) ?>
  <?cs each:message = messages ?>
    <li>
      <a name="<?cs var:message.id ?>"></a>
      <div class="id">
        Message #<?cs var:message.id ?>
      </div>
      <div class="body">
        <?cs var:message.body ?>
      </div>
      <div class="controls">
        <?cs if:trac.acl.DISCUSSION_APPEND ?>
          <a href="<?cs var:discussion.href ?>?discussion_action=add;message=<?cs var:message.id ?>#reply">Reply</a>
          <a href="<?cs var:discussion.href ?>?discussion_action=quote;message=<?cs var:message.id ?>#reply">Quote</a>
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
    </li>
    <?cs if:discussion.messages.0.id || args.discussion_action && !args.submit && (args.discussion_action != "delete") ?>
      <ul>
        <?cs call:display_topic(message.replies) ?>
        <?cs if:args.discussion_action && args.preview && args.message == message.id ?>
           <?cs call:display_preview() ?>
        <?cs /if ?>
        <?cs if:args.discussion_action && !args.submit && args.message == message.id ?>
          <?cs call:display_form() ?>
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
  <a name="-1"></a>
  <?cs if:!discussion.no_display && discussion.topic.id ?>
    <div class="topic">
      <div class="header">
        <div class="subject">
          <?cs var:discussion.topic.subject ?>
        </div>
        <div class="body">
          <?cs var:discussion.topic.body ?>
        </div>
        <div class="controls">
          <?cs if:trac.acl.DISCUSSION_APPEND ?>
            <a href="<?cs var:discussion.href ?>?discussion_action=add;#reply">Reply</a>
            <a href="<?cs var:discussion.href ?>?discussion_action=quote;#reply">Quote</a>
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
      </div>
      <?cs if:discussion.messages.0.id || args.discussion_action && !args.submit && (args.discussion_action != "delete") ?>
        <div class="replies">
          <ul>
            <?cs call:display_topic(discussion.messages) ?>
            <?cs if:args.discussion_action && args.preview && !args.message ?>
              <?cs call:display_preview() ?>
            <?cs /if ?>
            <?cs if:args.discussion_action && !args.submit && !args.message ?>
              <?cs call:display_form() ?>
            <?cs /if ?>
          </ul>
        </div>
      <?cs /if ?>
    </div>
   <?cs else?>
     <span>No discussion for this page created.</span>
   <?cs /if ?>
<?cs else ?>
  <span>You have no rights to see this discussion.</span>
<?cs /if ?>

<?cs if:trac.acl.DISCUSSION_MODERATE && discussion.is_moderator ?>
  <div class="buttons">
    <form method="get" action="<?cs var:discussion.href ?>">
      <input type="submit" name="deletetopic" value="Delete Topic" onclick="return confirm('Do you realy want to delete this topic?')"/>
      <input type="hidden" name="discussion_action" value="delete"/>
    </form>
    <?cs if:!discussion.no_navigation ?>
      <form method="get" action="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>">
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


