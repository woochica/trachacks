<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<h2>Manage Gringlets</h2>

<form method="post">
  <table class="listing">
    <thead>
      <tr>
        <th class="sel">&nbsp;</th>
        <th>Name</th>
      </tr>
    </thead>
    <tbody>
<?cs if:len(gringlets.list) ?>
<?cs   each:gringlet = gringlets.list ?>
<?cs     if:gringlet.permitted ?>
      <tr>
        <td class="sel">--</td>
        <td><a href="<?cs var:gringotts_href ?>/<?cs var:gringlet.name ?>"><?cs var:gringlet.name ?></a></td>
      </tr>
<?cs     else ?>
      <tr>
        <td class="sel">&nbsp;</td>
        <td><em><?cs var:gringlet.name ?></em></td>
      </tr>
<?cs     /if ?>
<?cs   /each ?>
<?cs else ?>
      <tr>
        <td class="sel">&nbsp;</td>
        <td>You do not have any Gringlets defined.</td>
      </tr>
<?cs /if ?>
    </tbody>
  </table>
</form>
<?cs include "footer.cs"?>
