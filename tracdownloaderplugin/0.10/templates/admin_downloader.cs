<?cs include:"downloads_cntx_nav.cs" ?>

<h2>Downloader admin</h2>

<?cs if:selected.0=='category' || !selected.0 ?>
     <?cs if:!selected.0 ?>
        <?cs set:iterator.1 = 2 ?>
     <?cs else ?>
        <?cs set:iterator.0 = 1 ?>
        <?cs set:iterator.1 = 2 ?>
     <?cs /if ?>
    <?cs each:cat_iter = iterator ?>
        <?cs if:cat_iter == 1 ?>
            <?cs set:heading = 'Edit' ?>
            <?cs set:hidden_id_name = 'edit_id' ?>
        <?cs else ?>
            <?cs set:heading = 'Add' ?>
            <?cs set:hidden_id_name = 'super_id' ?>
        <?cs /if ?>
        
        <form id="category" class="addnew" method="post" enctype="multipart/form-data">
         <fieldset>
          <legend><?cs var:heading ?> category:</legend>
          
          <input type="hidden" name="form_type" value = "category" />
          <input type="hidden" name="<?cs var:hidden_id_name ?>" value = "<?cs var:selected.1 ?>" />
          
          <div class="field">
            <label>Name: <br/>
                <input type="text" name="name" value = "<?cs 
                  if:cat_iter == 1 ?><?cs var:categories[selected.1].name ?><?cs 
                  /if ?>" />
            </label>
          </div>
          
          <div class="field">
            <label>Order: <br/>
                <input type="text" name="sort" value = "<?cs 
                  if:cat_iter == 1 ?><?cs var:categories[selected.1].sort ?><?cs 
                  /if ?>" />
            </label>
          </div>
          
          <div class="field">
            <label>Notes: <br/>
                <textarea rows="5" name="notes"><?cs 
                  if:cat_iter == 1 ?><?cs var:categories[selected.1].notes ?><?cs 
                  /if ?></textarea>
            </label>
          </div>
          
          <div class="buttons">
            <input type="submit" name="submit" value="Submit" />
            <?cs if:selected.0=='category' && cat_iter == 1 ?>
                <input type="submit" name="delete" value="Delete" />
            <?cs /if ?>
          </div>
         </fieldset>
        </form>
    <?cs /each ?>
<?cs /if ?>

<?cs if:selected.0=='release'||selected.0=='category'  ?>
    <?cs if:selected.0 == 'release' ?>
        <?cs set:heading = 'Edit' ?>
        <?cs set:hidden_id_name = 'edit_id' ?>
    <?cs else ?>
        <?cs set:heading = 'Add' ?>
        <?cs set:hidden_id_name = 'super_id' ?>
    <?cs /if ?>
    <form id="release" class="addnew" method="post" enctype="multipart/form-data">
     <fieldset>
      <legend><?cs var:heading ?> release:</legend>
      
      <input type="hidden" name="form_type" value = "release" />
      <input type="hidden" name="<?cs var:hidden_id_name ?>" value = "<?cs var:selected.1 ?>" />
      
      <div class="field">
        <label>Name: <br/>
            <input type="text" name="name" value = "<?cs 
                  if:selected.0 == 'release' ?><?cs var:releases[selected.1].name ?><?cs 
                  /if ?>" />
        </label>
      </div>
      
      <div class="field">
        <label>Order: <br/>
            <input type="text" name="sort" value = "<?cs 
                  if:selected.0 == 'release' ?><?cs var:releases[selected.1].sort ?><?cs 
                  /if ?>" />
        </label>
      </div>
      
      <div class="field">
        <label>Notes: <br/>
            <textarea rows="5" name="notes"><?cs 
                  if:selected.0 == 'release' ?><?cs var:releases[selected.1].notes ?><?cs 
                  /if ?></textarea>
        </label>
      </div>
      
      <div class="buttons">
        <input type="submit" name="submit" value="Submit" />
        <?cs if:selected.0=='release' ?>
           <input type="submit" name="delete" value="Delete" />
        <?cs /if ?>
      </div>
     </fieldset>
    </form>
<?cs /if ?>

<?cs if:selected.0=='file' || selected.0=='release'  ?>
    <?cs if:selected.0 == 'file' ?>
        <?cs set:heading = 'Edit' ?>
        <?cs set:hidden_id_name = 'edit_id' ?>
    <?cs else ?>
        <?cs set:heading = 'Add' ?>
        <?cs set:hidden_id_name = 'super_id' ?>
    <?cs /if ?>
    <form id="file" class="addnew" method="post" enctype="multipart/form-data">
     <fieldset>
      <legend><?cs var:heading ?> file:</legend>
      
      <input type="hidden" name="form_type" value = "file" />
      <input type="hidden" name="<?cs var:hidden_id_name ?>" value = "<?cs var:selected.1 ?>" />
      
      <?cs if:selected.0=='release' ?>
          <div class="field">
           <label>File: <br/><input type="file" name="file_to_upload"<?cs
             if:files_dir.readonly ?> disabled="disabled"<?cs /if ?> /></label>
          </div>
          <p class="help">
            <?cs if:files_dir.readonly ?>The web server does not have 
                sufficient permissions to store files in the files directory.
            <?cs else ?>
                Upload new file to release.
            <?cs /if ?>
          </p>
          
          <div class="field">
            <label>Name: <br/>
                <input type="text" name="name" value = "<?cs 
                      if:selected.0 == 'file' ?><?cs var:files[selected.1].name ?><?cs 
                      /if ?>" />
            </label>
          </div>
      <?cs else ?>
      
          <div class="field">
            <label>Change name: <br/>
                <input type="text" name="name" value = "<?cs 
                  if:selected.0 == 'file' ?><?cs var:files[selected.1].name ?><?cs 
                  /if ?>" />
            </label>
          </div>
      
      <?cs /if ?>
      
      <div class="field">
        <label>Order: <br/>
            <input type="text" name="sort" value = "<?cs 
                  if:selected.0 == 'file' ?><?cs var:files[selected.1].sort ?><?cs 
                  /if ?>" />
        </label>
      </div>
      
      <div class="field">
        <label>Architecture: <br/>
            <input type="text" name="architecture" value = "<?cs 
                  if:selected.0 == 'file' ?><?cs var:files[selected.1].architecture ?><?cs 
                  /if ?>" />
        </label>
      </div>
      
      <div class="field">
        <label>Notes: <br/>
            <textarea rows="5" name="notes"><?cs 
                  if:selected.0 == 'file' ?><?cs var:files[selected.1].notes ?><?cs 
                  /if ?></textarea>
        </label>
      </div>
      
      <div class="buttons">
       <input type="submit" name="submit" value="Submit"<?cs
         if:(admin.readonly && selected.0=='file') ?> disabled="disabled"<?cs /if ?> />
       <?cs if:selected.0=='file' ?>
         <input type="submit" name="delete" value="Delete"<?cs
            if:(admin.readonly && selected.0=='file') ?> disabled="disabled"<?cs /if ?> />
       <?cs /if ?>
      </div>
     </fieldset>
    </form>
<?cs /if ?>

<?cs include:"downloads_list.cs" ?>
