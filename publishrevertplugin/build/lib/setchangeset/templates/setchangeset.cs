<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="changeset">
<h1>Ticket <a href="../ticket/<?cs var:ticket_id ?>"><?cs var:ticket_id ?></a></h1>

<?cs def:node_change(item,cl,kind) ?><?cs 
  set:ndiffs = len(item.diff) ?><?cs
  set:nprops = len(item.props) ?>
  <div class="<?cs var:cl ?>"></div><?cs 
  if:cl == "rem" ?>
   <a title="Show what was removed (rev. <?cs var:item.rev.old ?>)" href="<?cs
     var:item.browser_href.old ?>"><?cs var:item.path.old ?></a><?cs
  else ?>
   <a title="Show entry in browser" href="<?cs
     var:item.browser_href.new ?>"><?cs var:item.path.new ?></a><?cs
  /if ?>
  <span class="comment">(<?cs var:kind ?>)</span><?cs
  if:item.path.old && item.change == 'copy' || item.change == 'move' ?>
   <small><em>(<?cs var:kind ?> from <a href="<?cs
    var:item.browser_href.old ?>" title="Show original file (rev. <?cs
    var:item.rev.old ?>)"><?cs var:item.path.old ?></a>)</em></small><?cs
  /if ?><?cs
  if:$ndiffs + $nprops > #0 ?>
    (<a href="#file<?cs var:name(item) ?>" title="Show differences"><?cs
      if:$ndiffs > #0 ?><?cs var:ndiffs ?>&nbsp;diff<?cs if:$ndiffs > #1 ?>s<?cs /if ?><?cs 
      /if ?><?cs
      if:$ndiffs && $nprops ?>, <?cs /if ?><?cs 
      if:$nprops > #0 ?><?cs var:nprops ?>&nbsp;prop<?cs if:$nprops > #1 ?>s<?cs /if ?><?cs
      /if ?></a>)<?cs
  elif:cl == "mod" ?>
    (<a href="<?cs var:item.browser_href.old ?>"
        title="Show previous version in browser">previous</a>)<?cs
  /if ?>
<?cs /def ?>

<dl id="overview">
 <dt class="time">Changesets</dt>
 <dd class="time"><?cs
 each:changeset = ticket.setchangesets ?>
  <a href="../changeset/<?cs var:changeset ?>"><?cs var:changeset ?></a><?cs
 /each ?></dd>
 <dt class="files">Files:</dt>
 <dd class="files">
  <ul><?cs each:item = setchangeset.changes ?>
   <li><?cs var:item.path.new ?> <?cs var:item.rev.new ?>
   </li>
  <?cs /each ?></ul>
  <br/><br/>
  <?cs each:item = setchangeset.changes ?>
   <?cs var:item.path.new ?> 
  <?cs /each ?>
 </dd>
</dl>

<div class="diff">
 <div id="legend">
  <h3>Legend:</h3>
  <dl>
   <dt class="unmod"></dt><dd>Unmodified</dd>
   <dt class="add"></dt><dd>Added</dd>
   <dt class="rem"></dt><dd>Removed</dd>
   <dt class="mod"></dt><dd>Modified</dd>
   <dt class="cp"></dt><dd>Copied</dd>
   <dt class="mv"></dt><dd>Moved</dd>
  </dl>
 </div>

</div>
<?cs include "footer.cs"?>
