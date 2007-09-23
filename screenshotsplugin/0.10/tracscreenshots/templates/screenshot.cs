<?cs include "header.cs" ?>

<div id="ctxtnav" class="nav">
</div>

<div id="content" class="screenshot">
  <h1><?cs var:screenshots.screenshot.file ?></h1>

  <table id="info" summary="Description">
    <tbody>
      <tr>
        <th scope="col">
          <?cs var:screenshots.screenshot.name ?>, <?cs var:screenshots.screenshot.width ?>x<?cs var:screenshots.screenshot.height ?> (added by <?cs var:screenshots.screenshot.author ?>, <?cs var:screenshots.screenshot.time ?> ago)
        </th>
      </tr>
      <tr>
        <td class="message">
          <?cs var:screenshots.screenshot.description ?>
        </td>
      </tr>
    </tbody>
  </table>

  <div id="preview">
    <p>
      <a href="<?cs var:screenshots.href ?>/<?cs var: screenshots.screenshot.id ?>?format=raw" title="<?cs var:screenshots.screenshot.name ?>">
        <img src="<?cs var:screenshots.href ?>/<?cs var: screenshots.screenshot.id ?>?format=raw" alt="<?cs var:screenshots.screenshot.description ?>" width="<?cs var:screenshots.screenshot.width ?>" height="<?cs var:screenshots.screenshot.height ?>"/>
      </a>
    </p>
  </div>

  <?cs if:trac.acl.SCREENSHOTS_ADMIN ?>
    <div class="buttons">
      <form method="post" action="<?cs var:screenshots.href ?>/">
        <div>
          <input type="submit" name="edit" value="Edit"/>
          <input type="hidden" name="action" value="edit"/>
          <input type="hidden" name="id" value="<?cs var:screenshots.screenshot.id ?>"/>
        </div>
      </form>
      <form method="post" action="<?cs var:screenshots.href ?>/">
        <div>
          <input type="submit" name="delete" value="Delete"/>
          <input type="hidden" name="id" value="<?cs var:screenshots.screenshot.id ?>"/>
          <input type="hidden" name="action" value="delete"/>
        </div>
      </form>
    </div>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
