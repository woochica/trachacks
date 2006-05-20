<?cs include "discussion-header.cs" ?>

<h1>
  <?cs var:discussion.forum.subject ?>
</h1>
<div class="forum-description">
  <?cs var:discussion.forum.description ?>
</div>
  <table>
    <tr>
      <th class="subject">Subject</th>
      <th class="author">Author</th>
      <th class="messages">Replies</th>
    </tr>
    <?cs each:topic = discussion.topics ?>
      <tr>
        <td class="subject">
          <a class="subject" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
            <?cs var:topic.subject ?>
          </a>
        </td>
        <td class="author">
          <a class="author" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
            <?cs var:topic.author ?>
          </a>
        </td>
        <td class="messages">
          <a class="messages" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
            <?cs var:topic.replies ?>
          </a>
        </td>
      </tr>
    <?cs /each ?>
  </table>

  <form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>">
    <div class="buttons">
      <input type="submit" name="newtopic" value="New Topic"/>
    </div>
    <input type="hidden" name="action" value="add"/>
  </form>

<?cs include "footer.cs" ?>
