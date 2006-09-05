<?cs include "macros.cs" ?>
<?cs include "my_macros.cs" ?>

<?cs include "discussion-header.cs" ?>

<h1>Forum #<?cs var:discussion.forum.id ?> - Topic List</h1>
<div class="name">
  <?cs var:discussion.forum.name ?>
</div>
<div class="description">
  <?cs var:discussion.forum.description ?>
</div>
<?cs if:discussion.topics.0.id ?>
  <table class="listing">
    <thead>
      <tr>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'id', 'ID', discussion.href + '/' + discussion.forum.id + '?') ?>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'subject', 'Subject', discussion.href + '/' + discussion.forum.id + '?') ?>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'author', 'Author', discussion.href + '/' + discussion.forum.id + '?') ?>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'lastreply', 'Last Reply', discussion.href + '/' + discussion.forum.id + '?') ?>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'time', 'Founded', discussion.href + '/' + discussion.forum.id + '?') ?>
        <?cs call:my_sortable_th(discussion.order, discussion.desc, 'replies', 'Replies', discussion.href + '/' + discussion.forum.id + '?') ?>
      </tr>
    </thead>
    </tbody>
      <?cs each:topic = discussion.topics ?>
        <tr class="<?cs if:name(topic) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
          <td class="id">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="id"><?cs var:topic.id ?></div>
            </a>
          </td>
          <td class="subject">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="subject"><?cs alt:topic.subject ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="author">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="author" ><?cs alt:topic.author ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="lastreply">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="lastreply"><?cs alt:topic.lastreply ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="founded">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="founded" ><?cs alt:topic.time ?>&nbsp;<?cs /alt ?></div>
            </a>
          </td>
          <td class="replies">
            <a href="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>/<?cs var:topic.id ?>">
              <div class="replies" ><?cs var:topic.replies ?></div>
            </a>
          </td>
        </tr>
      <?cs /each ?>
    </tbody>
  </table>
<?cs else ?>
  <p class="help">There are no topics created in this forum.</p>
<?cs /if ?>

<div class="buttons">
  <?cs if:trac.acl.DISCUSSION_APPEND ?>
    <form method="post" action="<?cs var:discussion.href ?>/<?cs var:discussion.forum.id ?>">
      <input type="submit" name="newtopic" value="New Topic"/>
      <input type="hidden" name="forum" value="<?cs var:discussion.forum.id ?>"/>
      <input type="hidden" name="discussion_action" value="add"/>
    </form>
  <?cs /if ?>
  <?cs if:trac.acl.DISCUSSION_ADMIN ?>
    <form method="post" action="<?cs var:discussion.href ?>">
      <input type="submit" name="deleteforum" value="Delete Forum" onclick="return confirm('Do you realy want to delete this forum?')"/>
      <input type="hidden" name="forum" value="<?cs var:discussion.forum.id ?>"/>
      <input type="hidden" name="discussion_action" value="delete">
    </form>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
