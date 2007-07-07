<h2>Subversion: Hooks</h2>


<form id="tooglestatus" class="addnew" method="post">
  <fieldset>
    <legend>Status</legend>
    <p class="help">Hook <?cs var:svnhooks.section ?> is currently <b style="color: black;"><?cs if:svnhooks.status ?>ACTIVE<?cs else ?>INACTIVE<?cs /if ?></b>.</p>
    <?cs if:svnhooks.note ?><p class="help" style="color: red;"><?cs var:svnhooks.note ?></p><?cs /if ?>
    <div class="buttons">
      <input type="submit" name="tooglestatus" <?cs if:svnhooks.status ?>disabled="disabled"<?cs /if ?> value=" Enable " />
      <input type="submit" name="tooglestatus" <?cs if:svnhooks.status==0 ?>disabled="disabled"<?cs /if ?> value=" Disable " />
      <input type="hidden" name="sections" value="<?cs var:svnhooks.section ?>" />
    </div>
  </fieldset>
</form>

<?cs if:svnhooks.section=='post-commit' ?><?cs include:"addtrac.cs" ?><?cs /if ?>

<?cs if:svnhooks.section=='post-commit' ?><?cs include:"addemail.cs" ?><?cs /if ?>
<?cs if:svnhooks.section=='post-revprop-change' ?><?cs include:"addemail.cs" ?><?cs /if ?>


<form id="changesection" method="post">
  <?cs call:hdf_select(svnhooks.sections, "sections", svnhooks.section, 0) ?> 
  <input type="submit" name="changesection" value=" Select " />
</form>

<form id="savehookfile" method="post">
  <div class="field">
    <textarea rows="20" style="width:63%" name="current"><?cs var:svnhooks.current ?></textarea>
  </div>
  <div class="buttons">
    <input type="hidden" name="sections" value="<?cs var:svnhooks.section ?>" />
    <input type="submit" name="savehookfile" value=" Apply changes " />
    <input type="reset" value=" Reset " />
  </div>
</form>

<br />

<h2>Documentation</h2>
<?cs if:svnhooks.description ?>
<h3><?cs var:svnhooks.section ?>.tmpl</h3>
<pre><?cs var:svnhooks.description ?></pre>
<?cs /if ?>
<h3>Links</h3>
<ul>
  <li><a href="http://svnbook.red-bean.com/nightly/en/svn.ref.reposhooks.<?cs var:svnhooks.section ?>.html">http://svnbook.red-bean.com/nightly/en/svn.ref.reposhooks.<?cs var:svnhooks.section ?>.html</a></li>
</ul>
