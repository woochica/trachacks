<?cs include "header.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="screenshots">
  <div class="title">
    <h1><?cs var:screenshots.title ?></h1>
  </div>

  <?cs var:screenshots.content ?>

  <?cs if:trac.acl.SCREENSHOTS_ADMIN ?>
    <div class="buttons screenshot_buttons">
      <form method="post" action="<?cs var:screenshots.href ?>/">
        <div>
          <input type="submit" name="add" value="Add"/>
          <input type="hidden" name="action" value="add"/>
          <input type="hidden" name="index" value="<?cs var:screenshots.index ?>"/>
        </div>
      </form>
      <?cs if:screenshots.id ?>
        <form method="post" action="<?cs var:screenshots.href ?>/">
          <div>
            <input type="submit" name="edit" value="Edit"/>
            <input type="hidden" name="action" value="edit"/>
            <input type="hidden" name="id" value="<?cs var:screenshots.id ?>"/>
            <input type="hidden" name="index" value="<?cs var:screenshots.index ?>"/>
          </div>
        </form>
        <form method="post" action="<?cs var:screenshots.href ?>/">
          <div>
            <input type="submit" name="delete" value="Delete"/>
            <input type="hidden" name="id" value="<?cs var:screenshots.id ?>"/>
            <input type="hidden" name="index" value="<?cs var:screenshots.index ?>"/>
            <input type="hidden" name="action" value="delete"/>
          </div>
        </form>
      <?cs /if ?>
    </div>
  <?cs /if ?>

  <?cs if:trac.acl.SCREENSHOTS_FILTER ?>
    <div class="filter">
      <form method="post" action="<?cs var:screenshots.href ?>/">
        <fieldset>
          <legend>
            Display filter:
          </legend>
          <div>
            <input type="hidden" name="action" value="display"/>
          </div>
        </fieldset>
      </form>
    </div>
  <?cs /if ?>

</div>

<?cs include "footer.cs" ?>
