<h2>Delete Ticket</h2>

<?cs if:ticketdelete.message ?>
<b><?cs var:ticketdelete.message ?></b><br />
<a href="<?cs var:ticketdelete.href ?>">Back</a>
<?cs else ?>
<p>
<b>Note: This is intended only for use in very odd circumstances.<br />
It is usually a better idea to resolve a ticket as invalid, than to remove it from the database.</b>
</p>

<form method="post" onsubmit="return confirm('Are you sure you want to do this?')">
Ticket ID: <input type="text" name="ticketid" /><br />
Again: <input type="text" name="ticketid2" /><br />
<input type="submit" value="Delete" />
</form>
<?cs /if ?>
