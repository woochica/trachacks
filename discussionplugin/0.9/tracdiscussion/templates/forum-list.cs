<?cs include "discussion-header.cs" ?>

<?cs def:display_group(group, forums) ?>
  <table class="listing">
    <thead>
      <?cs if:group.id ?>
        <tr>
          <th class="group" colspan="7">
            <div class="name"><?cs var:group.name ?></div>
            <div class="description"><?cs var:group.description ?></div>
          </th>
        <tr>
      <?cs /if ?>
      <tr>
        <th class="subject">Forum</th>
        <th class="moderators">Moderators</th>
        <th class="lasttopic">Last Topic</th>
        <th class="lastreply">Last Reply</th>
        <th class="founded">Founded</th>
        <th class="topics">Topics</th>
        <th class="replies">Replies</th>
      </tr>
    </thead>
    <tbody>
      <?cs each:forum = forums ?>
        <?cs if forum.group == group.id ?>
         <tr class="<?cs if:name(forum) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
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

<h1>Forum List</h1>

<?cs each:group = discussion.groups ?>
  <?cs if:group.forums ?>
    <?cs call:display_group(group, discussion.forums) ?>
  <?cs /if ?>
<?cs /each ?>

<?cs if:trac.acl.DISCUSSION_MODIFY ?>
  <div class="buttons">
    <form method="post" action="<?cs var:discussion.href ?>">
      <input type="submit" name="newforum" value="New Forum"/>
      <input type="hidden" name="discussion_action" value="add"/>
    </form>
  </div>
<?cs /if ?>

<?cs include "discussion-footer.cs" ?>
