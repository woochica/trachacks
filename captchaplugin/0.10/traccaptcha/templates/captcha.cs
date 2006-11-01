<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs if:error ?>
<div id="content" class="error">
 <h1>Captcha Error</h1>
 <p class="message"><?cs var:error ?></p>
<?cs else ?>
<div id="content" class="traccaptcha">
<?cs /if ?>
<form method="post" action="<?cs var:captcha.href ?>">
<?cs var:captcha.challenge ?>
Response: <input type="text" name="captcha_response"/>
<input type="submit" value="Submit"/>
</form>
</div>

<?cs include "footer.cs" ?>
