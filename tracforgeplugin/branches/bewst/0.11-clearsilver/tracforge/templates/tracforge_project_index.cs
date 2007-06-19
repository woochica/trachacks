<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
  <ul>
  </ul>
</div>

<div id="content" class="">
  <h1>Project Index</h1>
  
  <ul>
  <?cs each:project = tracforge.projects ?>
    <li>
    <?cs if:project.href ?>
      <a href="<?cs var:project.href ?>" title="<?cs var:project.description ?>">
        <?cs var:project.name ?>
      </a>
    <?cs else ?>
      <small><?cs var:project.name ?>: <em>Error</em> <br />
        (<?cs var:project.description ?>)
      </small>
    <?cs /if ?>
    </li>
  <?cs /each ?>
  </ul>
</div>

<?cs include "footer.cs" ?>