<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div class="guestbook">
  <h1>
    <?cs var:guestbook.title ?>
  </h1>
  <?cs each:message = guestbook.messages ?>
    <table class="message">
      <tr class="header">
        <th class="left">
          <?cs var:message.author ?>
        </th>
        <th class="right">
          <?cs var:message.time ?>
        </th>
      </tr>
      <tr class="header">
        <?cs if:trac.acl.GUESTBOOK_DELETE ?>
          <th class="left">
            <?cs var:message.title?>
          </th>
          <th class="right">
            <a href="/guestbook?action=delete;id=<?cs var:message.id ?>">
              Delete
            </a>
          </th>
        <?cs else ?>
          <th class="left" colspan="2">
            <?cs var:message.title?>
          </th>
        <?cs /if ?>
      </tr>
      <tr class="row">
        <td class="left" colspan="2">
          <?cs var:message.body ?>
        </td>
      </tr>
    </table>
  <?cs /each ?>

  <?cs if:trac.acl.GUESTBOOK_APPEND ?>
    <form class="append_form" method="post" action="<?cs var:trac.href.guestbook ?>">
      <fieldset>
        <legend>
          Add entry:<br>
        </legend>
        <div class="field">
          <label>
            Name:<br>
            <input type="text" name="author" value=""/>
          </label>
        </div>
        <div class="field">
          <label>
            Title:<br>
            <input class="textfield" type="text" name="title" value=""/>
          </label>
        </div>
        <div class="field">
          <label>
            Text:<br>
            <textarea class="textfield" name="text" rows="20">
Enter your message here...
            </textarea>
          </label>
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
