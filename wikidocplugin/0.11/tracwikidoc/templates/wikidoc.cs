<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<!-- $Id: wikidoc.cs 9864 2008-12-11 17:32:20Z cosimo $ -->

<?cs if:wikidoc.trail_last ?>
<div id="ctxtnav" class="nav">
<h2>PerlDoc Navigation</h2>
<ul>
<li><a href="<?cs var:trac.href.wikidoc ?>">Index</a></li>
<?cs each:component = wikidoc.trail ?>
<li><?cs var:component ?></li>
<?cs /each ?>
<li class="last"><?cs var:wikidoc.trail_last ?></li>
</ul>
<hr />
</div>
<?cs /if ?>


<div id="content" class="wikidoc">
<?cs var:wikidoc.content ?>
</div>

<?cs include "footer.cs" ?>
