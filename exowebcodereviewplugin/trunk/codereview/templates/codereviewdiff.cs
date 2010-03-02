<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs include "nav.cs" ?>
<div class="wiki">
<!--copy from wiki.cs:<div class="diff">-->
    <h1> CodeReview Changes between Version <?cs var:old_version ?> and <?cs var:version?> of r <?cs var:rev?> </h1>
    <form method="post" id="prefs" action="<?cs var:update.href?>">
    <div>
    <input type="hidden" name="action" value="diff" />
    <input type="hidden" name="version" value="<?cs var:version ?>" />
    <input type="hidden" name="old_version" value="<?cs var:old_version ?>" />

    <label>View differences <select name="style">
     <option value="inline"<?cs
       if:diff.style == 'inline' ?> selected="selected"<?cs
       /if ?>>inline</option>
     <option value="sidebyside"<?cs
       if:diff.style == 'sidebyside' ?> selected="selected"<?cs
       /if ?>>side by side</option>
    </select></label>
    <div class="field">
     Show <input type="text" name="contextlines" id="contextlines" size="2"
       maxlength="3" value="<?cs var:diff.options.contextlines ?>" />
     <label for="contextlines">lines around each change</label>
    </div>
    <fieldset id="ignore">
     <legend>Ignore:</legend>
     <div class="field">
      <input type="checkbox" id="blanklines" name="ignoreblanklines"<?cs
        if:diff.options.ignoreblanklines ?> checked="checked"<?cs /if ?> />
      <label for="blanklines">Blank lines</label>
     </div>
     <div class="field">
      <input type="checkbox" id="case" name="ignorecase"<?cs
        if:diff.options.ignorecase ?> checked="checked"<?cs /if ?> />
      <label for="case">Case changes</label>
     </div>
     <div class="field">
      <input type="checkbox" id="whitespace" name="ignorewhitespace"<?cs
        if:diff.options.ignorewhitespace ?> checked="checked"<?cs /if ?> />
      <label for="whitespace">White space changes</label>
     </div>
    </fieldset>
    <div class="buttons">
     <input type="submit" name="update" value="Update" />
    </div>
    </div>
    </form>
    <dl id="overview">
    <dt class="property comment">Status:</dt>
    <dd class="comment"><?cs var:version_status ?> </dd>
    <dt class="property author">Author:</dt>
    <dd class="author"> <?cs var:version_author ?> </dd>
    <dt class="property comment">Old_Status:</dt>
    <dd class="comment"><?cs var:oldversion_status ?> </dd>
    <dt class="property author">Old_Author:</dt>
    <dd class="author"> <?cs var:oldversion_author ?> </dd>
    <dt class="property time">Timestamp:</dt>
    <dd class="time"> <?cs var:ctime ?> </dd>   
    </dl>

    <div class="diff">
    <div id="legend">
     <h3>Legend:</h3>
     <dl>
     <dt class="unmod"></dt><dd>Unmodified</dd>
     <dt class="add"></dt><dd>Added</dd>
     <dt class="rem"></dt><dd>Removed</dd>
     <dt class="mod"></dt><dd>Modified</dd>
     </dl>
    </div>
    <ul class="entries">
    <li class="entry">
    <h2>Version Diff</h2>
      <?cs if:diff.style == 'sidebyside' ?>
        <table class="sidebyside" summary="Differences" frame="above">
        <colgroup class="l"><col class="lineno" /><col class="content" /></colgroup>
        <colgroup class="r"><col class="lineno" /><col class="content" /></colgroup>
        <thead><tr>
          <th colspan="2">Version <?cs var:old_version ?></th>
          <th colspan="2">Version <?cs var:version ?></th>
        </tr></thead>
        <?cs each:change = version.diff ?>
          <?cs call:diff_display(change, diff.style) ?>
        <?cs /each ?>
        </table>
      <?cs else ?>
        <table class="inline" summary="Differences" frame="above">
        <colgroup><col class="lineno" /><col class="lineno" /><col class="content" /></colgroup>
        <thead><tr>
        <th title="Version <?cs var:old_version ?>">v<?cs var:old_version ?></th>
        <th title="Version <?cs var:version ?>">v<?cs var:version ?></th>
        <th>&nbsp;</th>
        </tr></thead>
        <?cs each:change = version.diff ?>
          <?cs call:diff_display(change, diff.style) ?>
        <?cs /each ?>
        </table>
      <?cs /if ?>
    </li>
    </ul>
    </div>

</div>
<?cs include "footer.cs" ?>
