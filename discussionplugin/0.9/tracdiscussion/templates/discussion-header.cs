<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
  <h2>Wiki Navigation</h2>
  <ul>
    <?cs if:discussion.forum.id ?>
      <?cs if:discussion.topic.id ?>
        <li>
          <a href="<?cs var:trac.href.discussion ?>">Forum Index</a>
        </li>
        <?cs if:discussion.message.id ?>
          <li>
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>">
              <?cs var:discussion.forum.subject ?>
            </a>
          </li>
          <li class="last">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>">
              <?cs var:discussion.topic.subject ?>
            </a>
          </li>
        <?cs else ?>
          <li class="last">
            <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>">
              <?cs var:discussion.forum.subject ?>
            </a>
          </li>
        <?cs /if ?>
      <?cs else ?>
        <li class="last">
          <a href="<?cs var:trac.href.discussion ?>">Forum Index</a>
        </li>
      <?cs /if ?>
    <?cs /if ?>
  </ul>
  <hr/>
</div>

<div id="content" class="discussion">
<div id="<?cs var:discussion.mode ?>" class="<?cs var:discussion.mode ?>">
