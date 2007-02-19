<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs if:pydoc.trail_last ?>
<div id="ctxtnav" class="nav">
<h2>PyDoc Navigation</h2>
<ul>
<li><a href="<?cs var:trac.href.pydoc ?>">Index</a></li>
<?cs each:component = pydoc.trail ?>
<li><?cs var:component ?></li>
<?cs /each ?>
<li class="last"><?cs var:pydoc.trail_last ?></li>
</ul>
<hr />
</div>
<?cs /if ?>


<div id="content" class="pydoc">
<?cs var:pydoc.content ?>
</div>

<?cs include "footer.cs" ?>
