<form id="addemail" class="addnew" method="post">
  <fieldset>
    <legend>Add email notification</legend>
    <div class="field">
      <label>Subject prefix:</label><br />
      <input type="text" name="subject" value="<?cs var:svnhooks.project_name ?>"/>
      <br />
      <label>Filter (perl regexp):</label><br />
      <input size="40" type="text" name="filter" />
      <br />
      <label>Emails: </label><br />
      <textarea style="width: 100%" rows="5" type="text" name="emails"></textarea>
      <br />
    </div>
    <p class="help">
      Helper tool for adding the subversion email notification script
      <a href="http://svn.collab.net/repos/svn/trunk/tools/hook-scripts/commit-email.pl.in">commit-email.pl</a>.
    </p>
    <div class="buttons">
      <input type="hidden" name="sections" value="<?cs var:svnhooks.section ?>" />
      <input type="submit" name="addemail" value=" Add " />
    </div>
  </fieldset>
</form>
