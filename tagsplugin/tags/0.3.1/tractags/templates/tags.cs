<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="wiki">

<?cs if:tag.title
?><p>
<h1><?cs var:tag.title ?></h1>
<?cs /if ?><?cs var:tag.body ?>
</p>
</div>

<?cs include "footer.cs" ?>
