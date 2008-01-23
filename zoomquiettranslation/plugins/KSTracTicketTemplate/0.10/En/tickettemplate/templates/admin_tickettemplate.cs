<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Available Projects</title></head>
<body>

<h2>Ticket: Template</h2>



<form id="savetickettemplate" method="post">

  <div class="field"><label for="type">Type:</label> <?cs
   call:hdf_select(options, 'type', type, 0) ?>
    <input type="submit" name="loadtickettemplate" value=" Load " />
    <input type="submit" name="savetickettemplate" value=" Apply changes " />
    <input type="reset" value=" Reset " />  
  </div>

  <div class="field">
    <label for="description">Full description (you may use <a tabindex="42" href="<?cs
    var:$trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label><br />
    <textarea id="description" name="description" class="wikitext" rows="20" style="width:63%" name="tt_text"><?cs var:tt_text ?></textarea>
  </div>
  
</form>

 <script type="text/javascript" src="<?cs
   var:htdocs_location ?>js/wikitoolbar.js"></script>

</html>
