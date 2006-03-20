<h3>Plugins</h3>

<?cs if:hackinstall.message ?>
<div style="background-color: red"><?cs var:hackinstall.message ?></div>
<?cs /if ?>

<form method="post">
<table>
<tr>
    <td>Name</td>
    <td>Current</td>
    <td>Installed</td>
    <td>Description</td>
    <td>Dependencies</td>
</tr>
<?cs each:plugin = hackinstall.plugins ?>
<?cs if:plugin.current != 0 ?>
<tr>
    <td><?cs name:plugin ?></td>
    <td><?cs var:plugin.current ?></td>
    <td><?cs if:plugin.installed != -1 ?><?cs var:plugin.installed ?><?cs /if ?></td>
    <td><?cs var:plugin.description ?></td>
    <td><?cs var:plugin.deps ?></td>
    <td><input type="submit" name="install_<?cs name:plugin ?>" value="Install" /></td>
</tr>
<?cs /if ?>
<?cs /each ?>
</table>
</form>
