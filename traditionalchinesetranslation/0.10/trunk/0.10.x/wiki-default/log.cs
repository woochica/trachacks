<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="first <?cs if:len(chrome.links.prev)+len(chrome.links.next) == 0 ?>last<?cs /if ?>">
   <a href="<?cs var:log.browser_href ?>">最新版本</a>
  </li><?cs
  if:len(chrome.links.prev) ?>
   <li class="<?cs if:!len(chrome.links.next) ?> last<?cs /if ?>">
    &larr; <a href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
      var:chrome.links.prev.0.title ?>">較新版本</a>
   </li><?cs
  /if ?><?cs
  if:len(chrome.links.next) ?>
   <li class="last">
    <a href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
      var:chrome.links.next.0.title ?>">較早版本</a> &rarr;
   </li><?cs
  /if ?>
 </ul>
</div>


<div id="content" class="log">
 <h1><?cs call:browser_path_links(log.path, log) ?></h1>
 <form id="prefs" action="<?cs var:browser_current_href ?>" method="get">
  <div>
   <input type="hidden" name="action" value="<?cs var:log.mode ?>" />
   <label>顯示從版本 <input type="text" id="rev" name="rev" value="<?cs
    var:log.items.0.rev ?>" size="5" /></label>
   <label>後退到版本 <input type="text" id="stop_rev" name="stop_rev" value="<?cs
    var:log.stop_rev ?>" size="5" />的日誌</label>
   <br />
   <div class="choice">
    <fieldset>
     <legend>模式:</legend>
     <label for="stop_on_copy">
      <input type="radio" id="stop_on_copy" name="mode" value="stop_on_copy" <?cs
       if:log.mode != "follow_copy" || log.mode != "path_history" ?> checked="checked" <?cs
       /if ?> />
      文件複製處停止 
     </label>
     <label for="follow_copy">
      <input type="radio" id="follow_copy" name="mode" value="follow_copy" <?cs
       if:log.mode == "follow_copy" ?> checked="checked" <?cs /if ?> />
      包括文件複製
     </label>
     <label for="path_history">
      <input type="radio" id="path_history" name="mode" value="path_history" <?cs
       if:log.mode == "path_history" ?> checked="checked" <?cs /if ?> />
     只顯示增加,移動和刪除的
     </label>
    </fieldset>
   </div>
   <label><input type="checkbox" name="verbose" <?cs
    if:log.verbose ?> checked="checked" <?cs
    /if ?> /> 顯示完整日誌訊息 </label>
  </div>
  <div class="buttons">
   <input type="submit" value="刷新" 
          title="Warning: by updating, you will clear the page history" />
  </div>
 </form>

 <div class="diff">
  <div id="legend">
   <h3>Legend:</h3>
   <dl>
    <dt class="add"></dt><dd>增加</dd><?cs
    if:log.mode == "path_history" ?>
     <dt class="rem"></dt><dd>刪除</dd><?cs
    /if ?>
    <dt class="mod"></dt><dd>修改</dd>
    <dt class="cp"></dt><dd>複製或重命名</dd>
   </dl>
  </div>
 </div>

 <form  class="printableform" action="<?cs var:log.changeset_href ?>" method="get">
  <div class="buttons"><input type="submit" value="顯示修改" 
       title="顯示舊版本與新版本的區別(從上面選擇)" />
 </div>
 <table id="chglist" class="listing">
  <thead>
   <tr>
    <th class="diff"></th>
    <th class="change"></th>
    <th class="rev">版本</th>
    <th class="chgset">變更集</th>
    <th class="date">日期</th>
    <th class="author">作者</th>
    <th class="summary"><?cs if:!log.verbose ?>日誌訊息<?cs /if ?></th>
   </tr>
  </thead>
  <tbody><?cs
   set:indent = #1 ?><?cs
   set:idx = #0 ?><?cs
   each:item = log.items ?><?cs 
    if:name(item) % #2 ?><?cs
     set:even_odd = "odd" ?><?cs
    else ?><?cs
     set:even_odd = "even" ?><?cs
    /if ?><?cs
    if:item.copyfrom_path ?>
     <tr class="<?cs var:even_odd ?>">
      <td class="copyfrom_path" colspan="7" style="padding-left: <?cs var:indent ?>em">
       copied from <a href="<?cs var:item.browser_href ?>"><?cs var:item.copyfrom_path ?></a>:
      </td>
     </tr><?cs
     set:indent = indent + #1 ?><?cs
    elif:log.mode == "path_history" ?><?cs
      set:indent = #1 ?><?cs
    /if ?>
    <tr class="<?cs var:even_odd ?>">
     <td class="diff">
      <input type="radio" name="old" 
             value="<?cs var:item.path ?>@<?cs var:item.rev ?>" <?cs
          if:idx == #1 ?> checked="checked" <?cs /if ?> />
      <input type="radio" name="new" 
             value="<?cs var:item.path ?>@<?cs var:item.rev ?>" <?cs
          if:idx == #0 ?> checked="checked" <?cs /if ?> /></td>
     <td class="change" style="padding-left:<?cs var:indent ?>em">
      <a title="View log starting at this revision" href="<?cs var:item.log_href ?>">
       <span class="<?cs var:item.change ?>"></span>
       <span class="comment">(<?cs var:item.change ?>)</span>
      </a>
     </td>
     <td class="rev">
      <a href="<?cs var:item.browser_href ?>" 
         title="Browse at revision <?cs var:item.rev ?>">@<?cs var:item.rev ?></a>
     </td>
     <td class="chgset">
      <a href="<?cs var:item.changeset_href ?>"
         title="查看修改 [<?cs var:item.rev ?>]">[<?cs var:item.rev ?>]</a>
     </td>
     <td class="date"><?cs var:log.changes[item.rev].date ?></td>
     <td class="author"><?cs var:log.changes[item.rev].author ?></td>
     <td class="summary"><?cs
      if:!log.verbose ?><?cs var:log.changes[item.rev].message ?><?cs /if ?></td>
    </tr><?cs
    if:log.verbose ?>
    <tr class="<?cs var:even_odd ?> verbose">
     <td class="summary" colspan="7"><?cs var:log.changes[item.rev].message ?></td>
    </tr><?cs
    /if ?><?cs
    set:idx = idx + 1 ?><?cs
   /each ?>
  </tbody>
 </table><?cs
 if:len(log.items) > #10 ?>
  <div class="buttons"><input type="submit" value="查看修改" 
       title="Diff from Old Revision to New Revision (select them above)" />
  </div><?cs
 /if ?>
 </form><?cs
 if:len(links.prev) || len(links.next) ?><div id="paging" class="nav"><ul><?cs
  if:len(links.prev) ?><li class="first<?cs
   if:!len(links.next) ?> last<?cs /if ?>">&larr; <a href="<?cs
   var:links.prev.0.href ?>" title="<?cs
   var:links.prev.0.title ?>">Younger Revisions</a></li><?cs
  /if ?><?cs
  if:len(links.next) ?><li class="<?cs
   if:len(links.prev) ?>first <?cs /if ?>last"><a href="<?cs
   var:links.next.0.href ?>" title="<?cs
   var:links.next.0.title ?>">舊版本</a> &rarr;</li><?cs
  /if ?></ul></div><?cs
 /if ?>

 <div id="help">
  <strong>提示:</strong> 查看 <a href="<?cs var:trac.href.wiki
  ?>/ZhTracRevisionLog">版本日誌</a> 對本頁面的幫助.
 </div>

</div>
<?cs include "footer.cs"?>
