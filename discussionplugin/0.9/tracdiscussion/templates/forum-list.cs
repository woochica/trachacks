<?cs include "discussion-header.cs" ?>

<h1>Forum Index</h1>
<table>
  <tr>
    <th class="subject">Forum</th>
    <th class="topics">Topics</th>
    <th class="messages">Replies</th>
  </tr>
  <?cs each:forum = discussion.forums ?>
    <tr>
      <td class="subject">
        <a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
          <div class="subject">
            <?cs var:forum.subject ?>
          </div>
          <div class="description">
            <?cs var:forum.description ?>
          </div>
        </a>
      </td>
      <td class="topics">
        <a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
          <div class="topics">
            <?cs var:forum.topics ?>
          </div>
        </a>
      </td>
      <td class="messages">
        <a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
          <div class="messages">
            <?cs var:forum.replies ?>
          </div>
        </a>
      </td>
    </tr>
  <?cs /each ?>
</table>

<?cs if:trac.acl.DISCUSSION_MODIFY ?>
  <form method="post" action="<?cs var:trac.href.discussion ?>">
    <div class="buttons">
      <input type="submit" name="newforum" value="New Forum"/>
    </div>
    <input type="hidden" name="action" value="add"/>
  </form>
<?cs /if ?>

<?cs include "discussion-footer.cs" ?>
