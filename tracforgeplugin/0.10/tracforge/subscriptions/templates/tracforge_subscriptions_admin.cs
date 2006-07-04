<?cs each:type = tracforge.subscriptions ?>
<h3><?cs name:type ?></h3>
<ul>
<?cs each:sub = type ?>
<li><?cs var:sub ?></li>
<?cs /each ?>
</ul>
<?cs /each ?>
