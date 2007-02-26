<link rel="stylesheet" type="text/css" href="<?cs var:htdocs_location ?>traciwyg/wikiwyg.css" />
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Wikiwyg.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Toolbar.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Wysiwyg.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Wikitext.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Preview.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>traciwyg/Trac.js"></script>
<script type="text/javascript">
onload = function() {
  var wiki = document.getElementById('wikipage');
  Wikiwyg.Trac.setup_wikiwyg_section(wiki, '<?cs var:htdocs_location ?>');
  }
</script>
