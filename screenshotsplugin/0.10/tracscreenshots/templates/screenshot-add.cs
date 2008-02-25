<?cs include "header.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="screenshots">
  <div class="title">
    <h1><?cs var:screenshots.title ?></h1>
  </div>

  <form class="add_form" method="post" enctype="multipart/form-data" action="<?cs var:screenshots.href ?>">
    <fieldset>
      <legend>
        <?cs if:args.action == 'add' ?>
          Add Screenshot:
        <?cs else?>
          Edit Screenshot:
        <?cs /if ?>
      </legend>
      <div class="field">
        <label for="name">Name:</label><br/>
        <?cs if:args.action == 'add' ?>
          <input type="text" id="name" name="name" value=""/><br/>
        <?cs else ?>
          <input type="text" id="name" name="name" value="<?cs var:screenshots.screenshot.name ?>"/><br/>
        <?cs /if ?>
      </div>
      <div class="field">
        <label for="description">Description:</label><br/>
        <?cs if:args.action == 'add' ?>
          <input type="text" id="description" name="description" value=""/><br/>
        <?cs else ?>
          <input type="text" id="description" name="description" value="<?cs var:screenshots.screenshot.description ?>"/><br/>
        <?cs /if ?>
      </div>
      <?cs if:args.action == 'add' ?>
        <div class="field">
          <label for="image">Image File:</label><br/>
          <input type="file" id="image" name="image" value=""/><br/>
        </div>
      <?cs /if ?>
      <?cs if:screenshots.has_tags ?>
        <div class="field">
          <label for="tags">Additional tags:</label><br/>
          <?cs if:args.action == 'add' ?>
            <input type="text" id="tags" name="tags" value=""/><br/>
          <?cs else ?>
            <input type="text" id="tags" name="tags" value="<?cs var:screenshots.screenshot.tags ?>"/><br/>
          <?cs /if ?>
        </div>
      <?cs /if ?>
      <div class="field">
        <label for="components">Components:</label><br/>
        <select id="components" name="components" multiple="on">
          <?cs each:component = screenshots.components ?>
            <?cs set:selected = 0 ?>
            <?cs if:screenshots.screenshot.components.0 ?>
              <?cs each:component_name = screenshots.screenshot.components ?>
                <?cs if:component.name == component_name ?>
                  <?cs set:selected = 1 ?>
                <?cs /if ?>
              <?cs /each ?>
            <?cs /if ?>
            <?cs if:selected ?>
              <option value="<?cs var:component.name ?>" selected="selected"><?cs var:component.name ?></option>
            <?cs else ?>
              <option value="<?cs var:component.name ?>"><?cs var:component.name ?></option>
            <?cs /if ?>
          <?cs /each ?>
        </select><br/>
      </div>
      <div class="field">
        <label for="versions">Versions:</label><br/>
        <select id="versions" name="versions" multiple="on">
          <?cs each:version = screenshots.versions ?>
            <?cs set:selected = 0 ?>
            <?cs if:screenshots.screenshot.versions.0 ?>
              <?cs each:version_name = screenshots.screenshot.versions ?>
                <?cs if:version.name == version_name ?>
                  <?cs set:selected = 1 ?>
                <?cs /if ?>
              <?cs /each ?>
            <?cs /if ?>
            <?cs if:selected ?>
              <option value="<?cs var:version.name ?>" selected="selected"><?cs var:version.name ?></option>
            <?cs else ?>
              <option value="<?cs var:version.name ?>"><?cs var:version.name ?></option>
            <?cs /if ?>
          <?cs /each ?>
        </select><br/>
      </div>
      <div class="buttons">
        <input type="submit" name="submit" value="Submit"/>
        <input type="button" name="cancel" value="Cancel" onclick="history.back()"/>
        <input type="hidden" name="id" value="<?cs var:screenshots.screenshot.id ?>"/>
        <input type="hidden" name="index" value="<?cs var:screenshots.index ?>"/>
        <?cs if:args.action == 'add' ?>
          <input type="hidden" name="action" value="post-add"/>
        <?cs else ?>
          <input type="hidden" name="action" value="post-edit"/>
        <?cs /if ?>
      </div>
    </fieldset>
  </form>
</div>

<?cs include "footer.cs" ?>
