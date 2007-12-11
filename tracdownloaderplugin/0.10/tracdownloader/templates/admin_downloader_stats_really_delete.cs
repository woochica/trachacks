<h2>Really delete record '<?cs var:dwn_record.id ?>'?</h2>
<p>Do you really want to delete record id '<?cs var:dwn_record.id ?>' from <?cs
    var:dwn_record.timest ?> about file '<?cs var:dwn_record.file ?>'?</p>

<h3>Attributes of download record:</h3>
<table><?cs 
each:itm = dwn_record.items ?>
    <tr><td><strong><?cs var:itm.0 ?></strong></td><td><?cs var:itm.1 ?></td></tr><?cs 
/each ?>
</table>
<form method="POST" action="">
    <input type="hidden" name="redirect_back" value="<?cs var:dwn_record.redir ?>" />
    <input type="hidden" name="delete_id" value="<?cs var:dwn_record.id ?>" />
    <input type="submit" name="delete" value="Delete" />
    <input type="submit" name="navigate_back" value="Back" />
</form>
