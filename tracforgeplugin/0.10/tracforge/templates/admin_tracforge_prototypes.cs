<h2>TracForge Prototypes</h2>

<p>
    <a href="<?cs var:tracforge.href.configset ?>">Config sets</a>
</p>
<p>
    <a href="<?cs var:tracforge.href.new ?>">New prototype</a>
</p>

<h4>Known Steps</h4>
<ul>
<?cs each:step = tracforge.prototypes.steps ?>
    <li><?cs var:step ?></li>
<?cs /each ?>
</ul>
