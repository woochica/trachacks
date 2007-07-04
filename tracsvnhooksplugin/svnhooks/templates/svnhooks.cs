<h2>Subversion <?cs var:svnhooks.section ?> hook</h2>

<form id="status" class="addnew" method="post">
  <fieldset>
    <legend>Status</legend>
    <p>Hook <?cs var:svnhooks.section ?> is currently <b><?cs if:svnhooks.status ?>ACTIVE<?cs else ?>INACTIVE<?cs /if ?></b>.</p>
    <div class="buttons">
      <input type="submit" name="status" <?cs if:svnhooks.status ?>disabled="disabled"<?cs /if ?> value=" Enable " />
      <input type="submit" name="status" <?cs if:svnhooks.status==0 ?>disabled="disabled"<?cs /if ?> value=" Disable " />
    </div>
  </fieldset>
</form>

<form id="addemail" class="addnew" method="post">
  <fieldset>
    <legend>Append email notification</legend>
    <div class="field">
      <label>Subject prefix:</label><br />
      <input type="text" name="subject" />
      <br />
      <label>Filter (perl regexp):</label><br />
      <input size="40" type="text" name="filter" />
      <br />
      <label>E-mails: </label><br />
      <textarea style="width: 100%" rows="5" type="text" name="emails"></textarea>
      <br />
    </div>
    <p class="help">Helper tool for the SVN email notification script.</p>
    <div class="buttons">
      <input type="submit" name="add" value=" Add " />
    </div>
  </fieldset>
</form>

<?cs if:svnhooks.note ?><p><?cs var:svnhooks.note ?></p><?cs /if ?>
<form id="hook" method="post">
  <div class="field">
    <textarea rows="20" style="width:63%" name="current"><?cs var:svnhooks.current ?></textarea>
  </div>
  <div class="buttons">
    <input type="submit" name="apply" value=" Apply " />
    <input type="reset" value=" Reset " />
  </div>
</form>

<?cs if:svnhooks.description ?>
<br />
<h2>Help for <?cs var:svnhooks.section ?> hook</h2>
<pre><?cs var:svnhooks.description ?></pre>
<?cs /if ?>