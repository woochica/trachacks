<form class="mod" id="modbasic" method="post">
	<div class="field">
		<textarea name="Authz Contents"
					cols="80"
					rows="<?cs var:admin.authz.fieldlength ?>"
					wrap="off"
		><?cs var:admin.authz.contents ?></textarea>
	</div>
	<div class="buttons">
		<input type="submit" value="Apply changes">
		<input type="reset" value="Revert to stored">
	</div>
</form>
