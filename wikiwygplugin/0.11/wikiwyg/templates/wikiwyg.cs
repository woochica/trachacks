<link rel="stylesheet" type="text/css" href="<?cs var:htdocs_location ?>wikiwyg/wikiwyg.css" />
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Wikiwyg.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Toolbar.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Wysiwyg.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Wikitext.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Preview.js"></script>
<script type="text/javascript" src="<?cs var:htdocs_location ?>wikiwyg/Trac.js"></script>
<script type="text/javascript">
onload = function() {
  var wiki = document.getElementById('wikipage');
  Wikiwyg.Trac.setup_wikiwyg_section(wiki, '<?cs var:htdocs_location ?>');
  }
</script>
