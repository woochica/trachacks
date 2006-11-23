<h2>Manage Site Files</h2>

<form id="addfile" class="addnew" method="post" enctype="multipart/form-data">
 <fieldset>
  <legend>Upload File:</legend>
  <div class="field">
   <label>File: <input type="file" name="site_file" <?cs
     if:siteupload.readonly ?> disabled="disabled"<?cs /if ?> /></label>
  </div>
  <p class="help">
    <?cs if:siteupload.readonly ?>
        The web server does not have sufficient permissions to
        store files in the environment plugins directory.
    <?cs else ?>
        Upload a file to the htdocs directory of the trac environment.
    <?cs /if ?>
  </p>
  <div class="buttons">
   <input type="submit" name="upload" value="Upload"<?cs
     if:siteupload.readonly ?> disabled="disabled"<?cs /if ?> />
  </div>
 </fieldset>
</form>

<form method="post">
    <table class="listing" id="sitelist">
        <thead>
            <tr><th class="sel">&nbsp;</th><th>Filename</th><th>Size</th></tr>
        </thead>
        <tbody>
            <?cs each:file = siteupload.files ?>
            <tr>
                <td><input type="checkbox" name="sel" value="<?cs var:file.name ?>" /></td>
                <td><?cs var:file.link ?></td>
                <td><?cs var:file.size ?></td>
            </tr>
            <?cs /each ?>
        </tbody>
    </table>
    <div class="buttons">
        <input type="submit" name="delete" value="Delete selected files" <?cs
          if:siteupload.readonly ?> disabled="disabled"<?cs /if ?> />
    </div>
</form>
