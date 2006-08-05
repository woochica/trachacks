<?cs include "header.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="screenshots">
  <div class="title">
    <h1><?cs var:screenshots.title ?></h1>
  </div>

  <div class="header">
    <b>Component:</b> <?cs var:screenshots.component.name ?> <?cs if:screenshots.component.description ?>(<?cs var:screenshots.component.description ?>)<?cs /if?> <b>Version:</b> <?cs var:screenshots.version.name ?> <?cs if:screenshots.version.description ?>(<?cs var:screenshots.version.description ?>)<?cs /if ?>
  </div>

  <div class="images">
    <div class="previous">
      <?cs each screenshot = screenshots.previous ?>
        <?cs if:screenshot.id ?>
          <a href="<?cs var:screenshots.href?>?version=<?cs var:screenshots.version.id ?>;component=<?cs var:screenshots.component.id ?>;id=<?cs var:screenshot.id ?>">
            <img src="<?cs var:screenshots.href?>/<?cs var:screenshot.id ?>/small"/>
          </a>
        <?cs else ?>
          <a class="noimage" href="#"></a>
        <?cs /if ?>
      <?cs /each ?>
    </div>
    <?cs if:screenshots.current.0.id ?>
      <div class="current">
        <?cs each screenshot = screenshots.current ?>
          <div class="count">
            <?cs var:screenshots.index ?>&nbsp;/&nbsp;<?cs var:screenshots.count ?>
          </div>
          <div class="name">
            <?cs alt:screenshot.name ?>noname<?cs /alt ?> by <?cs alt:screenshot.author ?>anonymous<?cs /alt ?>
          </div>
          <a href="<?cs var:screenshots.href?>/<?cs var:screenshot.id ?>/large">
            <img src="<?cs var:screenshots.href?>/<?cs var:screenshot.id ?>/medium"/>
          </a>
          <div class="description">
            <?cs alt:screenshot.description ?>without description<?cs /alt ?>
          </div>
        <?cs /each ?>
      </div>
    <?cs else ?>
      <div class="empty">
        <span>No screenshots for this component and version inserted.</span>
      </div>
    <?cs /if ?>
    <div class="next">
      <?cs each screenshot = screenshots.next ?>
        <?cs if:screenshot.id ?>
        <a href="<?cs var:screenshots.href?>?component=<?cs var:screenshots.component.id ?>;version=<?cs var:screenshots.version.id ?>;id=<?cs var:screenshot.id ?>">
          <img src="<?cs var:screenshots.href?>/<?cs var:screenshot.id ?>/small"/>
          </a>
        <?cs else ?>
          <a class="noimage" href="#"></a>
        <?cs /if ?>
      <?cs /each ?>
    </div>
  </div>

  <div class="controls">
    <form method="post" action="<?cs var:screenshots.href ?>">
      <fieldset>
        <legend>
          Controls:
        </legend>
        <div class="field">
          <label for="component">Component:</label>
          <select id="component" name="component" onchange="form.submit()">
            <?cs each: component = screenshots.components ?>
              <?cs if:component.id == screenshots.component.id ?>
                <option value="<?cs var:component.id ?>" selected="selected"><?cs var:component.name ?></option>
              <?cs else ?>
                <option value="<?cs var:component.id ?>"><?cs var:component.name ?></option>
              <?cs /if ?>
            <?cs /each?>
          </select>
        </div>
        <div class="field">
          <label for="version">Version:</label>
          <select id="version" name="version" onchange="form.submit()">
            <?cs each: version = screenshots.versions ?>
              <?cs if:version.id == screenshots.version.id ?>
                <option value="<?cs var:version.id ?>" selected="selected"><?cs var:version.name ?></option>
              <?cs else ?>
                <option value="<?cs var:version.id ?>"><?cs var:version.name ?></option>
              <?cs /if ?>
            <?cs /each ?>
          </select>
        </div>
        <div>
          <input type="hidden" name="action" value="display"/>
        </div>
      </fieldset>
    </form>
    <?cs if:trac.acl.SCREENSHOTS_ADMIN ?>
      <div class="buttons">
        <form method="post" action="<?cs var:screenshots.href ?>">
          <div>
            <input type="submit" name="add" value="Add Screenshot"/>
            <input type="hidden" name="component" value="<?cs var:screenshots.component.id ?>"/>
            <input type="hidden" name="version" value="<?cs var:screenshots.version.id ?>"/>
            <input type="hidden" name="action" value="add"/>
          </div>
        </form>
        <?cs if:screenshots.current.0.id ?>
          <form method="post" action="<?cs var:screenshots.href ?>">
            <div>
              <input type="submit" name="edit" value="Edit Screenshot"/>
              <input type="hidden" name="component" value="<?cs var:screenshots.component.id ?>"/>
              <input type="hidden" name="version" value="<?cs var:screenshots.version.id ?>"/>
              <input type="hidden" name="id" value="<?cs var:screenshots.current.0.id ?>"/>
              <input type="hidden" name="action" value="edit"/>
            </div>
          </form>
          <form method="post" action="<?cs var:screenshots.href ?>"/>
            <div>
              <input type="submit" name="delete" value="Delete Screenshot"/>
              <input type="hidden" name="component" value="<?cs var:screenshots.component.id ?>"/>
              <input type="hidden" name="version" value="<?cs var:screenshots.version.id ?>"/>
              <input type="hidden" name="id" value="<?cs var:screenshots.current.0.id ?>"/>
              <input type="hidden" name="action" value="delete"/>
            </div>
          </form>
        <?cs /if ?>
      </div>
    <?cs /if ?>
  </div>
</div>

<?cs include "footer.cs" ?>
