<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Available Projects</title></head>
<body>

<h2>传票: 模板</h2>



<form id="savetickettemplate" action="tickettemplate" method="post">

  <div class="field"><label for="type">种类:</label> <?cs
   call:hdf_select(options, 'type', type, 0) ?>
    <input type="submit" name="loadtickettemplate" value=" 载入模板 " />
    <input type="submit" name="savetickettemplate" value=" 应用修改 " />
    <input type="reset" value=" 重置 " />  
  </div>

  <div class="field">
    <label for="description">完整描述 (<a tabindex="42" href="<?cs var:$trac.href.wiki ?>/WikiFormatting">Wiki格式</a> 帮助):</label><br />
    <textarea id="description" name="description" class="wikitext" rows="20" cols="66" name="tt_text"><?cs var:tt_text ?></textarea>
  <?cs
  if:description_preview ?>
   <fieldset id="preview">
    <legend>描述预览</legend>
    <?cs var:description_preview ?>
   </fieldset><?cs
  /if ?>
  </div>


 <script type="text/javascript" src="<?cs
   var:htdocs_location ?>js/wikitoolbar.js"></script>

 <div class="buttons">
  <input type="submit" name="preview" value="预览" accesskey="r" />&nbsp;
  <input type="submit" value="发送" />
 </div>
  
</form>



</html>
