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

  <table border="0" cellspacing="0" cellpadding="0">
    <tr>
      <th>User</th>
      <th>Activity</th>
      <th>Last Change</th>
    </tr>
    <?cs each:log = worklog.worklog ?>
    <tr>
      <td><?cs var:log.name ?></td>
      <?cs if:log.finished == #0 ?>
      <td><a href="<?cs var:log.ticket_url ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?></td>
      <?cs else ?>
      <td><em>Idle</em> <small>(Last worked on: <a href="<?cs var:log.ticket_url ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?>)</small></td>      
      <?cs /if ?>
      <td><?cs var:log.delta ?></td>
    </tr>
    <?cs /each ?>
  </table>
</div>
</form>
<?cs include "footer.cs"?>
