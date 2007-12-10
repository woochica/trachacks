<table class="listing<?cs if:(!in_adm&&!download_link && !subcount(quest))?> wide<?cs /if ?>">
  <thead>
    <tr>
      <th>Category</th>
      <th>Release</th>
      <th>Filename</th>
      <th>Size (kB)</th>
      <th>Architecture</th>
    </tr>
  </thead>
  <?cs set:row_num=1 ?>
  <?cs each:category = categories_list ?>
    <?cs if row_num % #2 ?>
      <?cs set:row_class = 'even' ?>
    <?cs else ?>
      <?cs set:row_class = 'odd' ?>
    <?cs /if ?>
    <tr class="<?cs var:row_class ?> category">
      <td colspan="5">
        <?cs if in_adm ?><a href="<?cs var:href.base ?>/category/<?cs var:category.id ?>"><?cs /if 
            ?><?cs var:category.name ?><?cs if in_adm ?></a><?cs /if ?>
        <?cs if !in_adm ?>
            <a href="<?cs var:href.base ?>/notes/category/<?cs var:category.id ?>">
                <img alt="Category notes" src="<?cs var:chrome.href ?>/downloader/img/notes.png" />
            </a>
        <?cs /if ?>
      </td>
    </tr>
    <?cs set:row_num = row_num + 1 ?>
    <?cs each:release = category.releases ?>
      <?cs if row_num % #2 ?>
        <?cs set:row_class = 'even' ?>
      <?cs else ?>
        <?cs set:row_class = 'odd' ?>
      <?cs /if ?>
      <tr class="<?cs var:row_class ?> release">
        <td>&nbsp;</td>
        <td colspan="4">
          <?cs if in_adm ?><a href="<?cs var:href.base ?>/release/<?cs var:release.id ?>"><?cs /if ?>
            <?cs var:release.name ?>
          <?cs if in_adm ?></a><?cs /if ?>
          <?cs if !in_adm ?>
            <a href="<?cs var:href.base ?>/notes/release/<?cs var:release.id ?>">
                <img alt="Release notes" src="<?cs var:chrome.href ?>/downloader/img/notes.png" />
            </a>
        <?cs /if ?>
          <small>(<?cs var:release.timestamp ?>)</small>
        </td>
      </tr>
      <?cs set:row_num = row_num + 1 ?>
      <?cs each:file = release.files ?>
        <?cs if row_num % #2 ?>
          <?cs set:row_class = 'even' ?>
        <?cs else ?>
          <?cs set:row_class = 'odd' ?>
        <?cs /if ?>
        <tr class="<?cs var:row_class ?> file">
          <td colspan="2">&nbsp;</td>
          <td>
            <a href="<?cs var:href.base ?>/file/<?cs var:file.id ?>">
              <?cs var:file.name_disp ?><?cs if:!file.name_disp ?>--<?cs /if ?>
            </a>
            <?cs if !in_adm ?>
                <a href="<?cs var:href.base ?>/notes/file/<?cs var:file.id ?>">
                    <img alt="File notes" src="<?cs var:chrome.href ?>/downloader/img/notes.png" />
                </a>
            <?cs /if ?>
          </td>
          <td class="right">
            <?cs var:file.size ?>
          </td>
          <td>
            <?cs var:file.architecture ?>
          </td>
        </tr>
        <?cs set:row_num = row_num + 1 ?>
      <?cs /each ?>
    <?cs /each ?>
  <?cs /each ?>
</table>
