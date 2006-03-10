<h3>Plugins</h3>

<table>
<tr><td>Name</td><td>Current</td></tr>
<?cs each:plugin = hackinstall.plugins ?>
<tr><td><?cs var:plugin.name ?></td><td><?cs var:plugin.current ?></td></tr>
<?cs /each ?>
</table>
