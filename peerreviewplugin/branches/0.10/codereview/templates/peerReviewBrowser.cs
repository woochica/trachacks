<?cs include "macros.cs" ?>

<?cs def:sortable_th(order, desc, class, title, href) ?>
 <th class="<?cs var:class ?><?cs if:order == class ?> <?cs
   if:desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
  <a title="Sort by <?cs var:class ?><?cs
    if:order == class && !desc ?> (descending)<?cs /if ?>" 
     href="<?cs var:href[class] ?>"><?cs var:title ?></a>
 </th>
 <?cs /def ?>

<div id="content" class="browser">
 <h2><?cs call:browser_path_links(browser.path, browser) ?></h2>

 <div id="jumprev">
   <input type="text" onkeypress="switchRev(event);" id="rev" name="rev" value="<?cs var:browser.revision ?>" size="4" />
 </div>

 <?cs if:browser.is_dir ?>
  <table class="listing" id="dirlist">
   <thead>
    <tr><?cs 
     call:sortable_th(browser.order, browser.desc, 'name', 'Name', browser.href) ?><?cs 
     call:sortable_th(browser.order, browser.desc, 'size', 'Size', browser.href) ?>
     <th class="rev">Rev</th><?cs 
     call:sortable_th(browser.order, browser.desc, 'date', 'Age', browser.href) ?>
     <th class="change">Last Change</th>
    </tr>
   </thead>
   <tbody style="overflow: auto; max-height: 400px">
    <?cs if:len(chrome.links.up) ?>
     <tr class="even">
      <td class="name" colspan="5">
       <a class="parent" title="Parent Directory" href="<?cs
         var:chrome.links.up.0.href ?>">../</a>
      </td>
     </tr>
    <?cs /if ?>
    <?cs each:item = browser.items ?>
     <?cs set:change = browser.changes[item.rev] ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="name"><?cs
       if:item.is_dir ?><?cs
        if:item.permission ?>
         <a class="dir" title="Browse Directory" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="dir" title="Access Denied" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       else ?><?cs
        if:item.permission != '' ?>
         <a class="file" title="View File" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="file" title="Access Denied" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       /if ?>
      </td>
      <td class="size"><?cs var:item.size ?></td>
      <td class="rev"><?cs if:item.permission != '' ?><a title="View Revision Log" href="<?cs
        var:item.log_href ?>"><?cs var:item.rev ?></a><?cs else ?><?cs var:item.rev ?><?cs /if ?></td>
      <td class="age"><span title="<?cs var:browser.changes[item.rev].date ?>"><?cs
        var:browser.changes[item.rev].age ?></span></td>
      <td class="change">
       <span class="author"><?cs var:browser.changes[item.rev].author ?>:</span>
       <span class="change"><?cs var:browser.changes[item.rev].message ?></span>
      </td>
     </tr>
    <?cs /each ?>
   </tbody>
  </table><?cs
 /if ?><?cs

 if:len(browser.props) || !browser.is_dir ?>
  <table id="info" summary="Revision info"><?cs
   if:!browser.is_dir ?><tr>
    <th scope="row">
     Revision <a href="<?cs var:file.changeset_href ?>"><?cs var:file.rev ?></a>
     (checked in by <?cs var:file.author ?>, <?cs var:file.age ?> ago)
    </th>
    <td class="message"><?cs var:file.message ?></td>
   </tr><?cs /if ?><?cs
   if:len(browser.props) ?><tr>
    <td colspan="2"><ul class="props"><?cs
     each:prop = browser.props ?>
      <li>Property <strong><?cs var:name(prop) ?></strong> set to <em><code><?cs
      var:prop ?></code></em></li><?cs
     /each ?>
    </ul></td><?cs
   /if ?></tr>
  </table><?cs
 /if ?><?cs
 
 if:!browser.is_dir ?>
    <div id="preview" style="overflow: auto; max-height: 400px"><?cs
   if:file.preview ?><?cs
    var:file.preview ?><?cs
   elif:file.max_file_size_reached ?>
	<br><br><strong>No HTML preview is available (the file size exceeds <?cs var:file.max_file_size ?> bytes) - you cannot add it to a code review</strong>.<br><br> 
   <?cs else ?>
	<br><br><strong>No HTML preview is available for this file - you cannot add it to a code review</strong>.<br><br><?cs
   /if ?>
  </div>
  <input type=button onclick="addFile('<?cs var:browser.path ?>')" value="Add File" disabled=true id="addFileButton">&nbsp;&nbsp;
  Start Line: <input type=text onkeypress="lineEnter(event);" value="" size="5" id="lineBox1" onchange="addButtonEnable();">&nbsp;&nbsp;
  End Line: <input type=text onkeypress="lineEnter(event);" value="" size="5" id="lineBox2" onchange="addButtonEnable();">
  <input type=hidden value=<?cs var:file.rev ?> id=fileRevVal>
<?cs
 /if ?>
</div>
