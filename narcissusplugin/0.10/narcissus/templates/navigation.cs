<div id="ctxtnav" class="nav">
  <ul>
    <li class="first">
      <?cs if:main == "yes" ?>Visualisation
      <?cs else ?><a href="<?cs var:trac.href.narcissus ?>">Visualisation</a>
      <?cs /if ?>
    </li>
    <li>
      <?cs if:config == "yes" ?>Configure
      <?cs else ?><a href="<?cs var:trac.href.configure ?>">Configure</a>
      <?cs /if ?>
    </li>
    <li class="last">
      <?cs if:user_guide == "yes" ?>User Guide
      <?cs else ?><a href="<?cs var:trac.href.user_guide ?>">User Guide</a>
      <?cs /if ?>
    </li>
  </ul>
  <hr />
</div>

