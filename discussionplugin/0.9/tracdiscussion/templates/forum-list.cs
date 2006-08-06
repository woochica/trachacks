<?cs include "macros.cs" ?>

<?cs def:display_group(group, forums) ?>
  <table class="listing">
    <thead>
      <?cs if:group.id ?>
        <tr>
          <th class="group" colspan="8">
            <div class="name"><?cs var:group.name ?></div>
            <div class="description"><?cs var:group.description ?></div>
          </th>
        <tr>
      <?cs /if ?>
      <tr>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'id', 'ID', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'subject', 'Forum', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'moderators', 'Moderators', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'lasttopic', 'Last Topic', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'lastreply', 'Last Reply', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'time', 'Founded', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'topics', 'Topics', discussion.href + '?') ?>
        <?cs call:sortable_th(discussion.order, discussion.desc, 'replies', 'Replies', discussion.href + '?') ?>
      </tr>
    </thead>
    <tbody>
      <?cs each:forum = forums ?>
        <?cs if forum.group == group.id ?>
          <tr class="<?cs if:name(forum) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
            <td class="id">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="id"><?cs var:forum.id ?></div>
              </a>
            </td>
            <td class="title">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="subject"><?cs alt:forum.subject ?>&nbsp;<?cs /alt ?></div>
                <div class="description"><?cs alt:forum.description ?>&nbsp;<?cs /alt ?></div>
              </a>
            </td>
            <td class="moderators">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="moderators"><?cs alt:forum.moderators ?>&nbsp;<?cs /alt ?></div>
              </a>
            </td>
            <td class="lasttopic">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="lasttopic"><?cs alt:forum.lasttopic ?>&nbsp;<?cs /alt ?></div>
              </a>
            </td>
            <td class="lastreply">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="lastreply"><?cs alt:forum.lastreply ?>&nbsp;<?cs /alt ?></div>
              </a>
            </td>
            <td class="founded">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
               <div class="founded"><?cs alt:forum.time ?>&nbsp;<?cs /alt ?></div>
              </a>
            </td>
            <td class="topics">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="topics"><?cs var:forum.topics ?></div>
              </a>
            </td>
            <td class="replies">
              <a href="<?cs var:discussion.href ?>/<?cs var:forum.id ?>">
                <div class="replies"><?cs var:forum.replies ?></div>
              </a>
            </td>
          </tr>
        <?cs /if ?>
      <?cs /each ?>
    </tbody>
  </table>
<?cs /def ?>

<?cs linclude "discussion-header.cs" ?>
<h1>Forum List</h1>

<?cs if:discussion.forums.0.id ?>
  <?cs each:group = discussion.groups ?>
    <?cs if:group.forums ?>
      <?cs call:display_group(group, discussion.forums) ?>
    <?cs /if ?>
  <?cs /each ?>
<?cs else ?>
  <p class="help">There are no forums created.</p>
<?cs /if ?>

<?cs if:trac.acl.DISCUSSION_ADMIN ?>
  <div class="buttons">
    <form method="post" action="<?cs var:discussion.href ?>">
      <input type="submit" name="newforum" value="New Forum"/>
      <input type="hidden" name="discussion_action" value="add"/>
    </form>
  </div>
<?cs /if ?>

<?cs linclude "discussion-footer.cs" ?>
