<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="tags">

<form id="expression" action="<?cs var:trac.href.tags ?>" method="get">
<label for="tag-expression">Filter tags:</label>
<input type="text" id="tag-expression" name="e" size="40" accesskey="t" value="<?cs var:tag.expression ?>">
<input type="submit" value="Filter Tags" name="filter">
<div><strong>Note:</strong> See <a href="http://muness.textdriven.com/trac/wiki/tags">TracTags</a> for information about using tag expressions.</div>
<?cs if:tag.expression.error ?>
<div id="expression-error"><strong>Error:</strong> <?cs var:tag.expression.error ?></div>
<?cs /if ?>
</form>


<?cs if:tag.title
?><p>
<h1><?cs var:tag.title ?></h1>
<?cs /if ?><?cs var:tag.body ?>
</p>
</div>

<?cs include "footer.cs" ?>
