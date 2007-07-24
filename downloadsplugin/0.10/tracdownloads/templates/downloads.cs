<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<?cs include "my_macros.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="downloads">
  <div class="title">
    <h1><?cs var:downloads.title ?></h1>
  </div>
  <?cs if:downloads.downloads.0.id ?>
    <table class="listing">
      <thead>
        <tr>
          <?cs call:my_sortable_th(downloads.order, downloads.desc, 'id', 'ID', downloads.href + '?') ?>
        </tr>
      </thead>
      <tbody>
        <?cs each:download = downloads.downloads ?>
          <tr class="<?cs if:download.id % #2 ?>even<?cs else ?>odd<?cs /if ?>">
            <td class="id">
              <a href="<?cs var:downloads.href ?>/<?cs var:download.id ?>">
                <div class="id"><?cs var:download.id ?></div>
              </a>
            </td>
          </tr>
        <?cs /each ?>
      </tbody>
    </table>
  <?cs else ?>
    <p class="help">There are no downloads created.</p>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
