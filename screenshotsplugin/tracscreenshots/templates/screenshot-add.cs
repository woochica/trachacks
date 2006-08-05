<?cs include "header.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="screenshots">
  <div class="title">
    <h1><?cs var:screenshots.title ?></h1>
  </div>

  <form class="add_form" method="post" enctype="multipart/form-data" action="<?cs var:screenshots.href ?>?component=<?cs var:screenshots.component.id ?>;version=<?cs var:screenshots.version.id ?>">
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
          <input type="text" id="name" name="name" value="<?cs var:screenshots.current.0.name ?>"/><br/>
        <?cs /if ?>
      </div>
      <div class="field">
        <label for="description">Description:</label><br/>
        <?cs if:args.action == 'add' ?>
          <input type="text" id="description" name="description" value=""/><br/>
        <?cs else ?>
          <input type="text" id="description" name="description" value="<?cs var:screenshots.current.0.description ?>"/><br/>
        <?cs /if ?>
      </div>
      <?cs if:args.action == 'add' ?>
        <div class="field">
          <label for="image">Image File:</label><br/>
          <input type="file" id="image" name="image" value=""/><br/>
        </div>
      <?cs /if ?>
      <div class="field">
        <label for="component">Component:</label><br/>
        <select id="component" name="component">
          <?cs each:component = screenshots.components ?>
            <?cs if:component.id == screenshots.component.id ?>
              <option value="<?cs var:component.id ?>" selected="selected"><?cs var:component.name ?></option>
            <?cs else?>
              <option value="<?cs var:component.id ?>"><?cs var:component.name ?></option>
            <?cs /if ?>
          <?cs /each ?>
        </select><br/>
      </div>
      <div class="field">
        <label for="version">Version:</label><br/>
        <select id="version" name="version">
          <?cs each:version = screenshots.versions ?>
            <?cs if:version.id == screenshots.version.id ?>
              <option value="<?cs var:version.id ?>" selected="selected"><?cs var:version.name ?></option>
            <?cs else ?>
              <option value="<?cs var:version.id ?>"><?cs var:version.name ?></option>
            <?cs /if ?>
          <?cs /each ?>
        </select><br/>
      </div>
      <div class="buttons">
        <input type="submit" name="submit" value="Submit"/>
        <input type="button" name="cancel" value="Cancel" onclick="history.back()"/>
        <input type="hidden" name="id" value="<?cs var:screenshots.current.0.id ?>"/>
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
