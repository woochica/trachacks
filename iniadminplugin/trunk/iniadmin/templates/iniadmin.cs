<h2>[<?cs var:iniadmin.section ?>]</h2>
<form method="post">
<?cs set:idx = 0 ?>
<table class="ini">
<?cs each:option = iniadmin.options ?>
<?cs if:idx % 3 == 0 ?><tr><?cs /if ?>
<td>
<fieldset class="col<?cs var:idx % 2 ?>">
<legend><?cs var:option.name ?></legend>
<?cs if:option.type == "extension" ?>
<select name="<?cs var:option.name ?>">
<?cs each:opt = option.options ?>
<option value="<?cs var:opt ?>"<?cs if:option.value == opt ?> selected="selected"<?cs /if ?>><?cs var:opt ?></option>
<?cs /each ?>
</select>
<?cs elif:option.type == "bool" ?>
<input type="radio" name="<?cs var:option.name ?>" value="true"<?cs if:option.value == "true"?> checked="checked"<?cs /if ?>/> true
<input type="radio" name="<?cs var:option.name ?>" value="false"<?cs if:option.value == "false"?> checked="checked"<?cs /if ?>/> false
<?cs else ?>
<input type="text" name="<?cs var:option.name ?>" value="<?cs var:option.value ?>"/>
<?cs /if ?>
<div class="help">
<?cs var:option.doc ?>
</div>
</fieldset>
</td>
<?cs if:idx % 3 == 2 ?></tr><?cs /if ?>
<?cs set:idx = idx + 1 ?>
<?cs /each ?>
<?cs if:idx % 3 != 0 ?>
<?cs loop:i = idx % 3, 2 ?><td></td><?cs /loop ?></tr>
<?cs /if ?>
</table>
<input type="submit" value="Apply changes"/>
</form>
