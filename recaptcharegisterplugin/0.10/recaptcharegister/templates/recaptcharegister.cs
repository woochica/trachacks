<?cs include "header.cs"?>
<?cs include "macros.cs"?>

    <div id="content" class="register">
      <h1>Register an account</h1>

      <?cs if registration_error ?>
      <div class="system-message" py:if="registration_error">
        <h2>Error</h2>
        <p><?cs var:registration_error ?></p>
      </div>
      <?cs /if ?>

      <div id="recaptcha_script"></div>
      
      <form method="post" id="acctmgr_registerform" action="">
        <fieldset>
          <legend>Required</legend>
          <div>
            <input type="hidden" name="action" value="create" />
            <label>Username:
              <input type="text" name="user" class="textwidget" size="20" />
            </label>
          </div>
          <div>
            <label>Password:
              <input type="password" name="password" class="textwidget" size="20" />
            </label>
          </div>
          <div>
            <label>Confirm Password:
              <input type="password" name="password_confirm"
                     class="textwidget" size="20" />
            </label>
          </div>
          <div>
            <script>
              var RecaptchaOptions = {
                  theme : "<?cs var:recaptcha_theme ?>"
              };
            </script>
	    <script type="text/javascript" src="<?cs var:recaptcha_server ?>/challenge?k=<?cs var:recaptcha_key ?>"></script>
	    <noscript>
		<iframe src="<?cs var:recaptcha_server ?>/noscript?k=<?cs var:recaptcha_key ?>" height="300" width="500" frameborder="0"></iframe><br />
		<textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
		<input type='hidden' name='recaptcha_response_field' value='manual_challenge' />
	    </noscript>
          </div>
        </fieldset>
        <fieldset>
          <legend>Optional</legend>
          <div>
            <label>Name:
              <input type="text" name="name" class="textwidget" size="20" />
            </label>
          </div>
          <div>
            <label>Email:
              <input type="text" name="email" class="textwidget" size="20" />
            </label>
            <p py:if="reset_password_enabled">Entering your email address will
            enable you to reset your password if you ever forget it.</p>
          </div>
        </fieldset>
        <input type="submit" value="Create account" />
      </form>
    </div>
<?cs include:"footer.cs"?>

