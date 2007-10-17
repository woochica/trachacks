<?cs include "header.cs"?>
<?cs include "macros.cs"?>
<!-- wl.user, s.value AS real_name, wl.starttime, wl.endtime, wl.ticket, t.summary, wl.comment -->
<div id="content" class="worklog">
  <a id="worklogmanual" href="<?cs var:worklog.usermanual_href ?>" ><?cs var:worklog.usermanual_title ?></a>
  <h2>
    Work Log for <?cs var:worklog.worklog[0].dispname ?>
  </h2>
  <table border="0" cellspacing="0" cellpadding="0" id="worklog_report">
    <tr>
      <th>Ticket</th>
      <th>Time</th>
      <th>Comment</th>
    </tr>
    <?cs each:log = worklog.worklog ?>
    <tr>
      <td><a class="<?cs var:log.status ?> ticket" href="<?cs var:worklog.ticket_href ?>/<?cs var:log.ticket ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?></td>
      <td><span id="worklog_time_delta"><?cs var:log.delta ?></span></td>
      <td><span id="worklog_comment"><?cs var:log.comment ?></span></td>
    </tr>
    <?cs /each ?>
  </table>
</div>

<div id="altlinks">  <h3>Download in other formats:</h3><ul><li class="first last"><a href="?format=csv" class="csv">CSV</a></li></ul></div>

<?cs include "footer.cs"?>
