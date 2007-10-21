<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<form method="post" action="<?cs var:worklog.href ?>" >
<div id="content" class="worklog">
  <a id="worklogmanual" href="<?cs var:worklog.usermanual_href ?>" ><?cs var:worklog.usermanual_title ?></a>
  <div id="messages" >
    <?cs each:item = worklog.messages ?>
      <div class="message" ><?cs var:item ?></div>
    <?cs /each ?>
  </div>

  <table border="0" cellspacing="0" cellpadding="0" id="worklog_report">
    <tr>
      <th>User</th>
      <th>Activity</th>
      <th>Time</th>
      <th>Comment</th>
    </tr>
    <?cs each:log = worklog.worklog ?>
    <tr>
      <td><a href="<?cs var:worklog.href ?>/users/<?cs var:log.user ?>"><?cs var:log.dispname ?></a></td>
      <?cs if:log.finished == #0 ?>
      <td><a class="<?cs var:log.status ?> ticket" href="<?cs var:worklog.ticket_href ?>/<?cs var:log.ticket ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?></td>
      <?cs else ?>
      <td><em>Idle</em> <small>(Last worked on: <a class="<?cs var:log.status ?> ticket" href="<?cs var:log.ticket_url ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?>)</small></td>
      <?cs /if ?>
      <td><span id="worklog_time_delta"><?cs var:log.delta ?></span></td>
      <td><span id="worklog_comment"><?cs var:log.comment ?></span></td>
    </tr>
    <?cs /each ?>
  </table>
</div>
</form>

<div id="altlinks">  <h3>Download in other formats:</h3><ul><li class="first last"><a href="?format=csv" class="csv">CSV</a></li></ul></div>

<?cs include "footer.cs"?>
