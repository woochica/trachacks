<?cs include "header.cs" ?>
<?cs include "downloads-macros.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="downloads">
  <div class="title">
    <h1><?cs var:downloads.title ?></h1>
  </div>

  <?cs var:downloads.description.1 ?>

  <?cs if:trac.acl.DOWNLOADS_ADMIN ?>
    <form method="post" action="<?cs var:downloads.href ?>">
      <fieldset>
        <legend>
          Edit Description:
        </legend>

        <?cs if:args.action == 'edit' ?>
          <div class="field">
            <textarea id="description" name="description" class="wikitext" rows="10" cols="78"><?cs var:downloads.description.0 ?></textarea>
          </div>
        <?cs /if ?>

        <div class="buttons">
          <input type="submit" name="submit" value="Edit"/>
          <?cs if:args.action == 'edit' ?>
            <input type="button" name="cancel" value="Cancel" onclick="location.replace('<?cs var:downloads.href ?>?order=<?cs var:downloads.order ?>;desc=<?cs var:downloads.desc ?>')"/>
            <input type="hidden" name="action" value="post-edit"/>
          <?cs else ?>
            <input type="hidden" name="action" value="edit"/>
          <?cs /if ?>
          <input type="hidden" name="order" value="<?cs var:downloads.order ?>"/>
          <input type="hidden" name="desc" value="<?cs var:downloads.desc ?>"/>
        </div>
      </fieldset>
    </form>
  <?cs /if ?>

  <?cs if:downloads.downloads.0.id ?>
    <div class="downloads-list">
      <table class="listing">
        <thead>
          <tr>
            <?cs if:downloads.visible_fields.id ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'id', 'ID', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.file ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'file', 'File', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.description ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'description', 'Description', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.size ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'size', 'Size', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.time ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'time', 'Uploaded', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.count ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'count', 'Downloads', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.author ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'author', 'Uploader', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.tags && downloads.has_tags ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'tags', 'Tags', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.component ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'component', 'Component', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.version ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'version', 'Version', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.architecture ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'architecture', 'Architecture', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.platform ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'platform', 'Platform', downloads.href) ?>
            <?cs /if ?>
            <?cs if:downloads.visible_fields.type ?>
              <?cs call:sortable_th(downloads.order, downloads.desc, 'type', 'Type', downloads.href) ?>
            <?cs /if ?>
          </tr>
        </thead>
        <tbody>
          <?cs each:download = downloads.downloads ?>
            <tr class="<?cs if:download.id % #2 ?>odd<?cs else ?>even<?cs /if ?>">
              <?cs if:downloads.visible_fields.id ?>
                <td class="id">
                  <div class="id">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.id ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.file ?>
                <td class="file">
                  <div class="file">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.file ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.description ?>
                <td class="description">
                  <div class="description">
                    <?cs var:download.description ?>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.size ?>
                <td class="size">
                  <div class="size">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.size ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.time ?>
                <td class="time">
                  <div class="time">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.time ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.count ?>
                <td class="count">
                  <div class="count">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.count ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.author ?>
                <td class="author">
                  <div class="author">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.author ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.tags && downloads.has_tags ?>
                <td class="tags">
                  <div class="tags">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.tags ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.component ?>
                <td class="component">
                  <div class="component">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.component ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.version ?>
                <td class="version">
                  <div class="version">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.version ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.architecture ?>
                <td class="architecture">
                  <div class="architecture">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.architecture.name ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.platform ?>
                <td class="platform">
                  <div class="platform">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.platform.name ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>

              <?cs if:downloads.visible_fields.type ?>
                <td class="type">
                  <div class="type">
                    <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                      <?cs var:download.type.name ?>
                    </a>
                  </div>
                </td>
              <?cs /if ?>
            </tr>
          <?cs /each ?>
        </tbody>
      </table>
    </div>
  <?cs else ?>
    <p class="help">There are no downloads created.</p>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
