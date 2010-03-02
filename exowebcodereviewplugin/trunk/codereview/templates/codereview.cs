<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs include "nav.cs" ?>


<div id="title" class="wiki">
<?cs if:main=='yes' ?>
  <h1>CodeReviewMain</h1>
<?cs elif:completed=='yes' ?>
  <h1>Completed</h1>
<?cs /if ?>
</div>


<table style="width:100%" >
  <tr>
    <td>
      <a href="<?cs var:main.href ?>#incoming">Awaiting code review</a> | <a href="<?cs var:main.href ?>#inprogress">Undergoing review</a> | <a href="<?cs var:completed.href ?>#completed">Completely reviewed</a>
    </td>

    <td >
      <form id="prefs" method="GET" action="<?cs var:search_href ?>">
        <table>
          <tr>
            <td>Author</td>
                    <td>: <input type="text" name="author" <?cs if:search_author ?>value="<?cs var:search_author ?>"<?cs /if ?> /></td>
          </tr>
          <tr>
            <td>Comment</td>
            <td>: <input type="text" name="comment" <?cs if:search_comment ?>value="<?cs var:search_comment ?>"<?cs /if ?> /></td>
          </tr>
          <tr>
            <td>Date</td>
            <td>: <input type="text" name="date" <?cs if:search_date ?>value="<?cs var:search_date ?>"<?cs /if ?> /></td>
          </tr>
          <tr>
            <td colspan="2">
            <input type="submit" name="submit" value="Search" /> <span style="color:gray" >(Date format : yyyymmdd)</span>
            <input type="hidden" name="action" value="search" />
            <?cs if:completed=='yes' ?><input type="hidden" name="completed" value="on" /><?cs /if ?>
          </tr>
        </table>
      </form>
    </td>
  </tr>
</table>

<br />


<?cs if:main=='yes' ?>
<a name="inprogress"></a>
<div id="content" class="wiki">
<fieldset>
<legend>Undergoing review, count: <?cs var:incompleted.len ?></legend>
<table class="listing">
  <thead>
    <tr>
      <th>changeset</th>
      <th>date</th>
      <th>review</th>
      <th>path</th>
      <th>comment</th>
    </tr>
  </thead>
  <tbody>
    <?cs each:item=incompleted.items ?>
      <tr <?cs if:item.priority=='critical' ?>style="background: #fdc; border-color: #e88; color: #a22"<?cs /if ?>>
        <td style="white-space:nowrap">
          <a href="<?cs var:item.url_cs ?>" title="ChangeSet: <?cs var:item.rev ?>"><?cs var:item.rev ?></a> <?cs var:item.author ?>
        </td>
        <td style="white-space:nowrap">
          <?cs var:item.ctime ?>
        </td>
        <td>
          <a href="<?cs var:item.url_cr ?>" title="CodeReview: <?cs var:item.rev ?>"><?cs var:item.reviewers ?></a>
        </td>
        <td>
          <?cs var:item.prefix ?>
        </td>
        <td>
          <?cs var:item.msg ?>
        </td>
      </tr>
    <?cs /each ?>
  </tbody>
</table>
</fieldset>

<br />
<br />
<br />
<br />


<a name="incoming"></a>
<fieldset>
<legend>Awaiting code review , count: <?cs var:missing.len ?></legend>

<form method="post" action="<?cs var:nntr_href ?>" id="incoming_form">

<table class="listing">
  <thead>
  <tr>
    <th> </th>
    <th>changeset</th>
    <th>date</th>
    <th>review</th>
    <th>path</th>
    <th>comment</th>
  </tr>
  </thead>
  <tbody>
  <?cs each:item=missing.items ?>
    <tr>
      <td>
        <input type=checkbox name="<?cs var:item.rev ?>">
      </td>
      <td style="white-space:nowrap">
        <a href="<?cs var:item.url_cs ?>" title="ChangeSet: <?cs var:item.rev ?>"><?cs var:item.rev ?></a> <?cs var:item.author ?>
      </td>
      <td style="white-space:nowrap">
        <?cs var:item.ctime ?>
      </td>
      <td>
          <a href="<?cs var:item.url_cr ?>" title="New codereview for changeset <?cs var:item.rev ?>">New</a>
      </td>
      <td>
        <?cs var:item.prefix ?>
      </td>
      <td>
        <?cs var:item.msg ?>
      </td>
    </tr>
  <?cs /each ?>
  </tbody>
  <tfoot>
  <tr>
    <td colspan="5" >
      <input type="submit" name="action" id="No need to review" value="No need to review" /> | <input
       type="submit" name="action" value="Set to critical" />
       <?cs if:search_author ?><input type="hidden" name="author" value="<?cs var:search_author ?>" /><?cs /if ?>
       <?cs if:search_comment ?><input type="hidden" name="comment" value="<?cs var:search_comment ?>" /><?cs /if ?>
       <?cs if:search_date ?><input type="hidden" name="date" value="<?cs var:search_date ?>" /><?cs /if ?>
    </td>
  </tr>
  </tfoot>
</table>
</form>
</fieldset>

<?cs /if ?>

<?cs if:completed=='yes' ?>
<a name="completed"></a>
<fieldset>
<legend>Completely reviewed, count: <?cs var:completed.len ?></legend>

<table class="listing">
  <thead>
    <tr>
      <th>changeset</th>
      <th>date</th>
      <th>reviewers</th>
      <th>path</th>
      <th>comment</th>
    </tr>
  </thead>
  <tbody>
    <?cs each:item=completed.items ?>
      <tr <?cs if:item.priority=='critical' ?>style="background: #fdc; border-color: #e88; color: #a22"<?cs /if ?>>
        <td style="white-space:nowrap">
          <a href="<?cs var:item.url_cs ?>" title="ChangeSet: <?cs var:item.rev ?>"><?cs var:item.rev ?></a> <?cs var:item.author ?>
        </td>
        <td style="white-space:nowrap">
          <?cs var:item.ctime ?>
        </td>
        <td>
          <a href="<?cs var:item.url_cr ?>" title="CodeReview: <?cs var:item.rev ?>"><?cs var:item.reviewers ?></a>
        </td>
        <td>
          <?cs var:item.prefix ?>
        </td>
        <td>
          <?cs var:item.msg ?>
        </td>
      </tr>
    <?cs /each ?>
  </tbody>
</table>

</fieldset>
<?cs /if ?>
</div>

<?cs include "footer.cs" ?>
