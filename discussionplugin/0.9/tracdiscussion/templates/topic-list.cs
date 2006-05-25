<?cs include "discussion-header.cs" ?>

<h1>
  <?cs var:discussion.forum.subject ?>
</h1>
<div class="forum-description">
  <?cs var:discussion.forum.description ?>
</div>
  <table class="listing">
    <thead>
      <tr>
        <th class="subject">Subject</th>
        <th class="author">Author</th>
        <th class="founded">Founded</th>
        <th class="replies">Replies</th>
      </tr>
    </thead>
    </tbody>
      <?cs each:topic = discussion.topics ?>
        <tr class="<?cs if:name(topic) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
          <td class="subject">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
              <div class="subject"><?cs var:topic.subject ?></div>
            </a>
          </td>
          <td class="author">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
              <div class="author" ><?cs var:topic.author ?></div>
            </a>
          </td>
          <td class="founded">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
              <div class="founded" ><?cs var:topic.time ?></div>
            </a>
          </td>
          <td class="replies">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>">
              <div class="replies" ><?cs var:topic.replies ?></div>
            </a>
          </td>
        </tr>
      <?cs /each ?>
    </tbody>
  </table>

  <form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>">
    <div class="buttons">
      <input type="submit" name="newtopic" value="New Topic"/>
    </div>
    <input type="hidden" name="action" value="add"/>
  </form>

<?cs include "footer.cs" ?>
