<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="login">
	<?cs if:login.error ?>
		<p class="message">
		<?cs var:login.error ?>
		</p>
	<?cs /if ?>
	<form id="login" action="<?cs var:login.action ?>" method="POST">
	<input type="hidden" name="ref" value="<?cs var:login.referer ?>" />
	<fieldset id="properties">
		<legend>Enter your username and password</legend>
		<table><tr>
			<th class="col1"><label for="username">Username:</label></th>
			
			<td><input type="text" name="username" id="username" class="textwidget" /></td></tr>
			<tr><th class="col1"><label for="password">Password:</label></th>
			<td><input type="password" name="password" id="password" class="textwidget" /></td></tr>
		</table>
	</fieldset>
	<div class="buttons">
		<input type="submit" name="login" value="Login" />&nbsp;
		<input type="reset" name="reset" value="Clear" />
	</div>
	</form>
</div>
<?cs include "footer.cs"?>
