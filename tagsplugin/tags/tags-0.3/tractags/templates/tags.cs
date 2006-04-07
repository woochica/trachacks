<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="wiki">

<?cs if:tag.name
?><p>
<h1>Objects tagged <i><?cs var:tag.name ?></i></h1>
<?cs /if ?><?cs var:tag.body ?>
</p>
</div>

<?cs include "footer.cs" ?>
