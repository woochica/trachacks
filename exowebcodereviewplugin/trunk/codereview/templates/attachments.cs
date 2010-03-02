<?cs if:codereview.attach_href || len(codereview.attachments) ?>
<h2>Attachments</h2><?cs
 if:len(codereview.attachments) ?><div id="attachments">
  <dl class="attachments"><?cs each:attachment = codereview.attachments ?>
   <dt><a href="<?cs var:attachment.href ?>" title="View attachment"><?cs
   var:attachment.filename ?></a> (<?cs var:attachment.size ?>) - added by <em><?cs
   var:attachment.author ?></em> on <?cs
   var:attachment.time ?>.</dt><?cs
   if:attachment.description ?>
    <dd><?cs var:attachment.description ?></dd><?cs
   /if ?><?cs
  /each ?></dl><?cs
 /if ?><?cs
 if:codereview.attach_href ?>
  <form method="get" action="<?cs var:codereview.attach_href ?>"><div>
   <input type="hidden" name="action" value="new" />
   <input type="submit" value="Attach File" />
  </div></form><?cs
 /if ?><?cs if:len(codereview.attachments) ?></div><?cs /if ?>
<?cs /if ?>
