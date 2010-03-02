<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs include "nav.cs" ?>

<div class="wiki">

<form method="get">
  <h1>Change History of <a href="<?cs var:history.href ?>">codereview r<?cs var:history.cr_id ?></a></h1>

  <?cs if:history.count>0 ?>
    <table class="listing">
      <thead>
        <tr>
          <th></th>
          <th>version</th>
          <th>author</th>
          <th>time</th>
          <th>status</th>
        </tr>
      </thead>
      <tbody>
        <?cs each:item=history.items ?>
          <tr>
            <td><input type="radio" name="old_version" value="<?cs var:item.version ?>"
                <?cs if:name(item) == 0 ?> checked="checked"<?cs /if ?> />
                <input type="radio" name="version" value="<?cs var:item.version ?>"
                <?cs if:name(item) == 1 ?> checked="checked"<?cs /if ?> />
            </td>
            <td><a href="<?cs var:item.cr_href ?>"><?cs var:item.version ?></a></td>
            <td><?cs var:item.author ?></td>
            <td><?cs var:item.time ?></td>
            <td><?cs var:item.status ?></td>
          </tr>
        <?cs /each ?>
      </tbody>
    </table>
    <br />
    <input type="button" value="Edit this codereview" onclick="window.location='<?cs var:history.edit_href ?>'" />
    <input type="submit" name="submit" value="View Changes" />
    <input type="hidden" name="action" value="diff"/>

  <?cs else ?>
    <h2>no change history of codereview r<?cs var:history.cr_id ?></h2>
    <br />
    <input type="button" value="Create this codereview" onclick="window.location='<?cs var:history.edit_href ?>'" />
  <?cs /if ?>
</form>
</div>

<?cs include "footer.cs" ?>
