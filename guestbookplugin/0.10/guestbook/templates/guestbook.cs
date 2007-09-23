<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
</div>

<div id="content" class="guestbook">
  <h1>
    <?cs var:guestbook.title ?>
  </h1>
  <?cs each:message = guestbook.messages ?>
    <div class="message">
      <div class="header">
        <div class="title">
          <?cs var:message.title ?>
        </div>
        <div class="body">
          <?cs var:message.body ?>
        </div>
      </div>
      <div class="controls">
        <?cs if:trac.acl.GUESTBOOK_DELETE ?>
          <a href="<?cs var:trac.href.guestbook ?>?action=delete;id=<?cs var:message.id ?>">Delete</a>
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
    </div>
  <?cs /each ?>

  <?cs if:trac.acl.GUESTBOOK_APPEND ?>
    <form class="append_form" method="post" action="<?cs var:trac.href.guestbook ?>">
      <fieldset>
        <legend>
          Add entry:<br/>
        </legend>
        <div class="field">
          <label for="author">Author:</label><br/>
          <input type="text" id="author" name="author" value=""/>
        </div>
        <div class="field">
          <label for="title">Title:</label><br/>
          <input type="text" id="title" name="title" value=""/>
        </div>
        <div class="field">
          <label for="text">Text:</label><br/>
          <textarea class="wikitext" id="text" name="text" rows="10" cols="78">
Enter your message here...
          </textarea>
        </div>
        <input type="hidden" name="action" value="newentry"/>
        <div class="buttons">
          <input type="submit" name="submit" value="Submit"/>
        </div>
      </fieldset>
    </form>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
