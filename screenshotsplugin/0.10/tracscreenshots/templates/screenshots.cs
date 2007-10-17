<?cs include "header.cs" ?>

<div id="ctxtnav">
</div>

<div id="content" class="screenshots">
  <div class="title">
    <h1><?cs var:screenshots.title ?></h1>
  </div>

  <?cs include:screenshots.content_template ?>

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

          <fieldset>
            <legend>
              Components:
            </legend>

            <div>
              <?cs each:component = screenshots.components ?>
                <?cs if:screenshots.enabled_components[component.name] ?>
                  <input type="checkbox" name="components" value="<?cs var:component.name ?>" checked="yes"> <?cs var:component.name ?>
                <?cs else ?>
                  <input type="checkbox" name="components" value="<?cs var:component.name ?>"> <?cs var:component.name ?>
                <?cs /if ?>
              <?cs /each ?>
              <input type="button" name="all" value="All" onclick="check_all('components', true)"/>
              <input type="button" name="none" value="None" onclick="check_all('components', false)"/>
            </div>
          </fieldset>

          <fieldset>
            <legend>
              Versions:
            </legend>

            <div>
              <?cs each:version = screenshots.versions ?>
                <?cs if:screenshots.enabled_versions[version.name] ?>
                  <input type="checkbox" name="versions" value="<?cs var:version.name ?>" checked="yes"> <?cs var:version.name ?>
                <?cs else ?>
                  <input type="checkbox" name="versions" value="<?cs var:version.name ?>"> <?cs var:version.name ?>
                <?cs /if?>
              <?cs /each ?>
              <input type="button" name="all" value="All" onclick="check_all('versions', true)"/>
              <input type="button" name="none" value="None" onclick="check_all('versions', false)"/>
            </div>
          </fieldset>

          <div class="buttons">
            <input type="submit" name="filter" value="Apply Filter"/>
            <input type="hidden" name="action" value="filter"/>
          </div>

        </fieldset>
      </form>
    </div>
  <?cs /if ?>

</div>

<?cs include "footer.cs" ?>
