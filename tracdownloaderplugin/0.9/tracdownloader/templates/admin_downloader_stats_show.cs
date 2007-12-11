<h2>Download record list:</h2>
<p>List of download's attributes. There are shown only non-empty ones.</p>

<table><?cs 
each:itm = dwn_record.items ?>
    <tr><td><strong><?cs var:itm.0 ?></strong></td><td><?cs var:itm.1 ?></td></tr><?cs 
/each ?>
</table>
<form method="POST" action="">
    <input type="hidden" name="redirect_back" value="<?cs var:dwn_record.redir ?>" />
    <input type="submit" name="navigate_back" value="Back" />
</form>
