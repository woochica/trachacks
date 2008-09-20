<div class="header">
</div>

<div class="images">
  <table>
    <tbody>
      <?cs each row = screenshots.matrix ?>
        <tr>
          <?cs each:image = row ?>
            <td>
              <?cs if:image.id != -1 ?>
                <div class="image">
                  <a href="<?cs var:screenshots.href ?>/<?cs var:image.id ?>" title="<?cs var:image.name ?>">
                    <img src="<?cs var:screenshots.href ?>/<?cs var:image.id ?>?width=<?cs var:screenshots.width ?>;height=<?cs var:screenshots.height ?>;format=raw"
                      alt="<?cs var:image.description ?>" width="<?cs var:screenshots.width ?>" height="<?cs var:screenshots.height ?>"/>
                  </a>
                </div>
              <?cs else ?>
                <div class="image noimage" style="width: <?cs var:screenshots.width ?>px; height: <?cs var:screenshots.height ?>px">
                  &nbsp;
                </div>
              <?cs /if ?>
              <div class="name"><?cs alt:image.name ?>&nbsp;<?cs /alt ?></div>
              <?cs if:trac.acl.SCREENSHOTS_ADMIN ?>
                <div class="controls">
                  <?cs if:image.id != -1 ?>
                    <a href="<?cs var:screenshots.href ?>?action=edit;id=<?cs var:image.id ?>;index=<?cs var:screenshots.index ?>">Edit</a>
                    <a href="<?cs var:screenshots.href ?>?action=delete;id=<?cs var:image.id ?>;index=<?cs var:screenshots.index ?>">Delete</a>
                  <?cs else ?>
                    &nbsp;
                  <?cs /if ?>
                </div>
              <?cs /if ?>
            </td>
          <?cs /each?>
        </tr>
      <?cs /each?>
    </tbody>
  </table>
</div>

<div class="controls">
  <?cs if:screenshots.prev_index != -1 ?>
    <a href="<?cs var:screenshots.href ?>?index=<?cs var:screenshots.prev_index ?>">&larr; Previous Page</a>
  <?cs else ?>
    &larr; Previous Page
  <?cs /if?>
    &nbsp;<?cs var:screenshots.page ?>/<?cs var:screenshots.page_count ?>&nbsp;
  <?cs if:screenshots.next_index != -1 ?>
    <a href="<?cs var:screenshots.href ?>?index=<?cs var:screenshots.next_index ?>">Next Page &rarr;</a>
  <?cs else ?>
    Next Page &rarr;
  <?cs /if?>
</div>
