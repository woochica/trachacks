<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
<h2>PyDoc Navigation</h2>
<ul>
<li><a href="<?cs var:trac.href.pydoc ?>">Index</a></li>
<?cs if:pydoc.current ?>
<li><?cs var:pydoc.current ?></li>
<?cs /if ?>
</ul>
<hr />
</div>


<div id="content" class="tracpydoc">
<?cs var:pydoc.content ?>
</div>

<?cs include "footer.cs" ?>
