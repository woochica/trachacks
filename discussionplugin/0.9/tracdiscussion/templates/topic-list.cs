<?cs include "discussion-header.cs" ?>

<h1><?cs var:discussion.forum.subject ?> - Topic List</h1>
<div class="forum-description"><?cs var:discussion.forum.description ?></div>
  <table class="listing">
    <thead>
      <tr>
        <th class="subject">Subject</th>
        <th class="author">Author</th>
        <th class="lastreply">Last Reply</th>
        <th class="founded">Founded</th>
        <th class="replies">Replies</th>
      </tr>
    </thead>
    </tbody>
      <?cs each:topic = discussion.topics ?>
        <tr class="<?cs if:name(topic) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
          <td class="subject">
            <a href="<?cs var:discussion.href ?>/<?cs var:topic.id ?>">
              <div class="subject"><?cs alt:topic.subject ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="author">
            <a href="<?cs var:discussion.href ?>/<?cs var:topic.id ?>">
              <div class="author" ><?cs alt:topic.author ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="lastreply">
            <a href="<?cs var:discussion.href ?>/<?cs var:topic.id ?>">
              <div class="lastreply"><?cs alt:topic.lastreply ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="founded">
            <a href="<?cs var:discussion.href ?>/<?cs var:topic.id ?>">
              <div class="founded" ><?cs alt:topic.time ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="replies">
            <a href="<?cs var:discussion.href ?>/<?cs var:topic.id ?>">
              <div class="replies" ><?cs var:topic.replies ?></div>
            </a>
          </td>
        </tr>
      <?cs /each ?>
    </tbody>
  </table>

  <div class="buttons">
    <form method="post" action="<?cs var:discussion.href ?>">
      <input type="submit" name="newtopic" value="New Topic"/>
      <input type="hidden" name="discussion_action" value="add"/>
    </form>
    <?cs if:trac.acl.DISCUSSION_MODIFY ?>
      <form method="post" action="<?cs var:discussion.href ?>">
        <input type="submit" name="deleteforum" value="Delete Forum" onClick="return confirm('Do you realy want to delete this forum?')"/>
        <input type="hidden" name="discussion_action" value="delete">
      </form>
    <?cs /if ?>
  </div>

<?cs include "footer.cs" ?>
