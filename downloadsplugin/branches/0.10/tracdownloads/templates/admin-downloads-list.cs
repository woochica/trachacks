<?cs include "downloads-macros.cs" ?>

<h2>Downloads</h2>

<?cs if:downloads.download.id ?>
  <form id="edit-download-form" class="addnew" method="post" action="<?cs var:downloads.href ?>">
<?cs else ?>
  <form id="add-download-form" class="addnew" method="post" enctype="multipart/form-data" action="<?cs var:downloads.href ?>">
<?cs /if ?>
  <fieldset>
    <legend>
      <?cs if:downloads.download.id ?>
        Edit Download:
      <?cs else ?>
        Add Download:
      <?cs /if ?>
    </legend>

    <?cs if:!downloads.download.id ?>
      <div class="field">
        <label for="file">File:</label><br/>
        <input type="file" id="file" name="file" value=""/><br/>
      </div>
    <?cs /if ?>

    <div class="field">
      <label for="description">Description:</label><br/>
      <input type="text" id="description" name="description" value="<?cs var:downloads.download.description ?>"/><br/>
    </div>

    <?cs if:downloads.has_tags ?>
      <div class="field">
        <label for="tags">Additional Tags:</label><br/>
        <input type="text" id="tags" name="tags" value="<?cs var:downloads.download.tags ?>"/><br/>
      </div>
    <?cs /if ?>

    <div class="component">
      <label for="component">Component:</label><br/>
      <select id="component" name="component">
        <?cs each:component = downloads.components ?>
          <?cs if:downloads.download.component == component.name?>
            <option value="<?cs var:component.name ?>" selected="selected"><?cs var:component.name ?></option>
          <?cs else?>
            <option value="<?cs var:component.name ?>"><?cs var:component.name ?></option>
          <?cs /if ?>
        <?cs /each ?>
      </select><br/>
    </div>

    <div class="version">
      <label for="version">Version:</label><br/>
      <select id="version" name="version">
        <?cs each:version = downloads.versions ?>
          <?cs if:downloads.download.version == version.name?>
            <option value="<?cs var:version.name ?>" selected="selected"><?cs var:version.name ?></option>
          <?cs else?>
            <option value="<?cs var:version.name ?>"><?cs var:version.name ?></option>
          <?cs /if ?>
        <?cs /each ?>
      </select><br/>
    </div>

    <div class="architecture">
      <label for="architecture">Architecture:</label><br/>
      <select id="architecture" name="architecture">
        <?cs each:architecture = downloads.architectures ?>
          <?cs if:downloads.download.architecture == architecture.id ?>
            <option value="<?cs var:architecture.id ?>" selected="selected"><?cs var:architecture.name ?></option>
          <?cs else?>
            <option value="<?cs var:architecture.id ?>"><?cs var:architecture.name ?></option>
          <?cs /if ?>
        <?cs /each ?>
      </select><br/>
    </div>

    <div class="platform">
      <label for="platform">Platform:</label><br/>
      <select id="platform" name="platform">
        <?cs each:platform = downloads.platforms ?>
          <?cs if:downloads.download.platform == platform.id ?>
            <option value="<?cs var:platform.id ?>" selected="selected"><?cs var:platform.name ?></option>
          <?cs else?>
            <option value="<?cs var:platform.id ?>"><?cs var:platform.name ?></option>
          <?cs /if ?>
        <?cs /each ?>
      </select><br/>
    </div>

    <div class="type">
      <label for="type">Type:</label><br/>
      <select id="type" name="type">
        <?cs each:type = downloads.types ?>
          <?cs if:downloads.download.type == type.id ?>
            <option value="<?cs var:type.id ?>" selected="selected"><?cs var:type.name ?></option>
          <?cs else?>
            <option value="<?cs var:type.id ?>"><?cs var:type.name ?></option>
          <?cs /if ?>
        <?cs /each ?>
      </select><br/>
    </div>

    <div class="buttons">
      <?cs if:downloads.download.id ?>
        <input type="submit" name="submit" value="Edit"/>
        <input type="button" name="cancel" value="Cancel" onclick="location.href = '<?cs var:downloads.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>'"/>
        <input type="hidden" name="id" value="<?cs var:downloads.download.id ?>"/>
        <input type="hidden" name="action" value="post-edit"/>
      <?cs else ?>
        <input type="submit" name="submit" value="Add"/>
        <input type="hidden" name="action" value="post-add"/>
      <?cs /if ?>
      <input type="hidden" name="order" value="<?cs var:downloads.order ?>"/>
      <input type="hidden" name="desc" value="<?cs var:downloads.desc ?>"/>
    </div>
  </fieldset>
</form>

<?cs if:downloads.downloads.0.id ?>
  <form method="post" action="<?cs var:discussion.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
    <table class="listing">
      <thead>
        <tr>
          <th class="sel">&nbsp;</th>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'id', 'ID', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'file', 'File', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'description', 'Description', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'size', 'Size', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'time', 'Uploaded', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'count', 'Downloads', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'author', 'Uploader', downloads.href) ?>
          <?cs if:downloads.has_tags ?>
            <?cs call:sortable_th(downloads.order, downloads.desc, 'tags', 'Tags', downloads.href) ?>
          <?cs /if ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'component', 'Component', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'version', 'Version', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'architecture', 'Architecture', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'platform', 'Platform', downloads.href) ?>
          <?cs call:sortable_th(downloads.order, downloads.desc, 'type', 'Type', downloads.href) ?>
        </tr>
      </thead>
      <tbody>
        <?cs each:download = downloads.downloads ?>
          <tr class="<?cs if:download.id % #2 ?>odd<?cs else ?>even<?cs /if ?>">
            <td class="sel">
              <input type="checkbox" name="selection" value="<?cs var:download.id ?>"/>
            </td>

            <td class="id">
              <div class="id">
                <a href="<?cs var:downloads.href?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.id ?>
                </a>
              </div>
            </td>

            <td class="file">
              <div class="file">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.file ?>
                </a>
              </div>
            </td>

            <td class="description">
              <div class="description">
                <?cs var:download.description ?>
              </div>
            </td>

            <td class="size">
              <div class="size">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.size ?>
                </a>
              </div>
            </td>

            <td class="time">
              <div class="time">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.time ?>
                </a>
              </div>
            </td>

            <td class="count">
              <div class="count">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.count ?>
                </a>
              </div>
            </td>

            <td class="author">
              <div class="author">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.author ?>
                </a>
              </div>
            </td>

            <?cs if:downloads.has_tags ?>
              <td class="tags">
                <div class="tags">
                  <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                    <?cs var:download.tags ?>
                  </a>
                </div>
              </td>
            <?cs /if ?>

            <td class="component">
              <div class="component">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.component ?>
                </a>
              </div>
            </td>

            <td class="version">
              <div class="version">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.version ?>
                </a>
              </div>
            </td>

            <td class="architecture">
              <div class="architecture">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.architecture.name ?>
                </a>
              </div>
            </td>

            <td class="platform">
              <div class="platform">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.platform.name ?>
                </a>
              </div>
            </td>

            <td class="type">
              <div class="type">
                <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>">
                  <?cs var:download.type.name ?>
                </a>
              </div>
            </td>
          </tr>
        <?cs /each ?>
      </tbody>
    </table>

    <div class="buttons">
      <input type="submit" name="remove" value="Remove selected items" />
      <input type="hidden" name="action" value="delete"/>
    </div>
  </form>
<?cs else ?>
  <p class="help">As long as you don't add any items to the list, this field
    will remain completely hidden from the user interface.</p>
  <br style="clear: right"/>
<?cs /if ?>
