<?cs include:"header.cs" ?>
<?cs include:"macros.cs" ?>
<script type="text/javascript">
addEvent(window, 'load', function() { document.getElementById('summary').focus()}); 
</script>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="ticket">
<h1>兴建传票</h1>
<?cs include:"site_newticket.cs" ?>
<form id="newticket" method="post" action="<?cs
  var:trac.href.newticket ?>#preview">
 <?cs if:trac.authname == "anonymous" ?>
  <div class="field">
   <label for="reporter">您的用户名  或者  邮件地址:</label><br />
   <input type="text" id="reporter" name="reporter" size="40" value="<?cs
     var:newticket.reporter ?>" /><br />
  </div>
 <?cs /if ?>
 <div class="field">
  <label for="summary">简短描述:</label><br />
  <input id="summary" type="text" name="summary" size="80" value="<?cs
    var:newticket.summary ?>"/>
 </div><?cs
 if:len(newticket.fields.type.options) ?>
  <div class="field"><label for="type">种类:</label> <?cs
   call:hdf_select(newticket.fields.type.options, 'type',
                   newticket.type, 0) ?>
  </div><?cs
 /if ?>
 <div class="field">
  <label for="description">完整描述 (<a tabindex="42" href="<?cs
    var:$trac.href.wiki ?>/ZhWikiFormatting">维基格式说明</a>帮助):</label><br />
  <textarea id="description" name="description" class="wikitext" rows="10" cols="78">
<?cs var:newticket.description ?></textarea><?cs
  if:newticket.description_preview ?>
   <fieldset id="preview">
    <legend>描述预览</legend>
    <?cs var:newticket.description_preview ?>
   </fieldset><?cs
  /if ?>
 </div>

 <fieldset id="properties">
  <legend>传票选项</legend>
  <input type="hidden" name="action" value="create" />
  <input type="hidden" name="status" value="new" />
  <table><tr><?cs set:num_fields = 0 ?><?cs
  each:field = newticket.fields ?><?cs
   if:!field.skip ?><?cs
    set:num_fields = num_fields + 1 ?><?cs
   /if ?><?cs
  /each ?><?cs set:idx = 0 ?><?cs
   each:field = newticket.fields ?><?cs
    if:!field.skip ?><?cs set:fullrow = field.type == 'textarea' ?><?cs
     if:fullrow && idx % 2 ?><?cs set:idx = idx + 1 ?><th class="col2"></th><td></td></tr><tr><?cs /if ?>
     <th class="col<?cs var:idx % 2 + 1 ?>"><?cs
       if:field.type != 'radio' ?><label for="<?cs var:name(field) ?>"><?cs
       /if ?><?cs alt:field.label ?><?cs var:field.name ?><?cs /alt ?>:<?cs
       if:field.type != 'radio' ?></label><?cs /if ?></th>
     <td<?cs if:fullrow ?> colspan="3"<?cs /if ?>><?cs
      if:field.type == 'text' ?><input type="text" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="<?cs var:newticket[name(field)] ?>" /><?cs
      elif:field.type == 'select' ?><select id="<?cs
        var:name(field) ?>" name="<?cs var:name(field) ?>"><?cs
        if:field.optional ?><option></option><?cs /if ?><?cs
        each:option = field.options ?><option<?cs
         if:option == newticket[name(field)] ?> selected="selected"<?cs /if ?>><?cs
         var:option ?></option><?cs
        /each ?></select><?cs
      elif:field.type == 'checkbox' ?><input type="hidden" name="checkbox_<?cs
        var:name(field) ?>" /><input type="checkbox" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="1"<?cs
        if:newticket[name(field)] ?> checked="checked"<?cs /if ?> /><?cs
      elif:field.type == 'textarea' ?><textarea id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>"<?cs
        if:field.height ?> rows="<?cs var:field.height ?>"<?cs /if ?><?cs
        if:field.width ?> cols="<?cs var:field.width ?>"<?cs /if ?>><?cs
        var:newticket[name(field)] ?></textarea><?cs
      elif:field.type == 'radio' ?><?cs set:optidx = 0 ?><?cs
       each:option = field.options ?><label><input type="radio" id="<?cs
         var:name(field) ?>" name="<?cs
         var:name(field) ?>" value="<?cs var:option ?>"<?cs
         if:ticket[name(field)] == option ?> checked="checked"<?cs /if ?> /> <?cs
         var:option ?></label> <?cs set:optidx = optidx + 1 ?><?cs
       /each ?><?cs
      /if ?></td><?cs
     if:idx % 2 || fullrow ?><?cs
      if:idx < num_fields - 1 ?></tr><tr><?cs
      /if ?><?cs 
     elif:idx == num_fields - 1 ?><th class="col2"></th><td></td><?cs
     /if ?><?cs set:idx = idx + #fullrow + 1 ?><?cs
    /if ?><?cs
   /each ?></tr>
  </table>
 </fieldset>

 <script type="text/javascript" src="<?cs
   var:htdocs_location ?>js/wikitoolbar.js"></script>

 <?cs if newticket.can_attach ?><p>
  <label><input type="checkbox" name="attachment"<?cs
    if:newticket.attachment ?> checked="checked"<?cs /if ?> />
    本传票要带附件
  </label>
 </p><?cs
 /if ?>

 <div class="buttons">
  <input type="submit" name="preview" value="预览" accesskey="r" />&nbsp;
  <input type="submit" value="发送" />
 </div>
</form>

<div id="help">
 <strong>提示:</strong> 查看本页相关帮助 <a href="<?cs
   var:trac.href.wiki ?>/ZhTracTickets">传票</a> 
</div>
</div>

<?cs include "footer.cs" ?>
