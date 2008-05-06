<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Wiki Navigation</h2>
 <ul><?cs
  if:wiki.action == "diff" ?>
   <li class="first"><?cs
     if:len(chrome.links.prev) ?> &larr;
      <a class="prev" href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
       var:chrome.links.prev.0.title ?>">上一版本</a><?cs
     else ?>
      <span class="missing">&larr; 上一版本</span><?cs
     /if ?>
   </li>
   <li><a href="<?cs var:wiki.history_href ?>">頁面修改歷史</a></li>
   <li class="last"><?cs
     if:len(chrome.links.next) ?>
      <a class="next" href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
       var:chrome.links.next.0.title ?>">下一版本</a> &rarr; <?cs
     else ?>
      <span class="missing">下一版本 &rarr;</span><?cs
     /if ?>
   </li><?cs
  elif:wiki.action == "history" ?>
   <li class="last"><a href="<?cs var:wiki.current_href ?>">最新版本</a></li><?cs
  else ?>
   <li><a href="<?cs var:trac.href.wiki ?>">首頁</a></li>
   <li><a href="<?cs var:trac.href.wiki ?>/ZhTitleIndex">標題索引</a></li>
   <li><a href="<?cs var:trac.href.wiki ?>/ZhRecentChanges">日期索引</a></li>
   <li class="last"><a href="<?cs var:wiki.last_change_href ?>">最後修改版本</a></li><?cs
  /if ?>
 </ul>
 <hr />
</div>

<div id="content" class="wiki">

 <?cs if wiki.action == "delete" ?><?cs
  if:wiki.version - wiki.old_version > 1 ?><?cs
   set:first_version = wiki.old_version + 1 ?><?cs
   set:version_range = "versions "+first_version+" to "+wiki.version+" of " ?><?cs
   set:delete_what = "those versions" ?><?cs
  elif:wiki.version ?><?cs
   set:version_range = "version "+wiki.version+" of " ?><?cs
   set:delete_what = "此版本" ?><?cs
  else ?><?cs
   set:version_range = "" ?><?cs
   set:delete_what = "頁面" ?><?cs
  /if ?>
  <h1>Delete <?cs var:version_range ?><a href="<?cs
    var:wiki.current_href ?>"><?cs var:wiki.page_name ?></a></h1>
  <form action="<?cs var:wiki.current_href ?>" method="post">
   <input type="hidden" name="action" value="delete" />
   <p><strong>您確定要把此頁面<?cs
    if:!?wiki.version ?>版本<?cs
    /if ?>刪除<?cs var:version_range ?>?</strong><br /><?cs
   if:wiki.only_version ?>
    This is the only version the page, so the page will be removed
    completely!<?cs
   /if ?><?cs
   if:?wiki.version ?>
    <input type="hidden" name="version" value="<?cs var:wiki.version ?>" /><?cs
   /if ?><?cs
   if:wiki.old_version ?>
    <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" /><?cs
   /if ?>
   This is an irreversible operation.</p>
   <div class="buttons">
    <input type="submit" name="cancel" value="取消" />
    <input type="submit" value="刪除 <?cs var:delete_what ?>" />
   </div>
  </form>

 <?cs elif:wiki.action == "diff" ?>
  <h1>變化: <?cs
    if:wiki.old_version ?>從 <a href="<?cs var:wiki.current_href ?>"><?cs var:wiki.page_name ?>的</a>
     <a href="<?cs var:wiki.current_href ?>?version=<?cs var:wiki.old_version?>">版本 <?cs var:wiki.old_version?></a> 和 <?cs
    else ?>從<?cs
    /if ?>
    <a href="<?cs var:wiki.current_href ?>?version=<?cs var:wiki.version?>">版本 <?cs var:wiki.version?></a>之間的變化
    </h1>
  <form method="post" id="prefs" action="<?cs var:wiki.current_href ?>">
   <div>
    <input type="hidden" name="action" value="diff" />
    <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
    <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" />
    <label>查看方式 <select name="style">
     <option value="inline"<?cs
       if:diff.style == 'inline' ?> selected="selected"<?cs
       /if ?>>內嵌方式</option>
     <option value="sidebyside"<?cs
       if:diff.style == 'sidebyside' ?> selected="selected"<?cs
       /if ?>>兩列方式</option>
    </select></label>
    <div class="field">
     修改處顯示 <input type="text" name="contextlines" id="contextlines" size="2"
       maxlength="3" value="<?cs var:diff.options.contextlines ?>" />
     <label for="contextlines">行</label>
    </div>
    <fieldset id="ignore">
     <legend>忽略:</legend>
     <div class="field">
      <input type="checkbox" id="blanklines" name="ignoreblanklines"<?cs
        if:diff.options.ignoreblanklines ?> checked="checked"<?cs /if ?> />
      <label for="blanklines">空行</label>
     </div>
     <div class="field">
      <input type="checkbox" id="case" name="ignorecase"<?cs
        if:diff.options.ignorecase ?> checked="checked"<?cs /if ?> />
      <label for="case">大小寫區別</label>
     </div>
     <div class="field">
      <input type="checkbox" id="whitespace" name="ignorewhitespace"<?cs
        if:diff.options.ignorewhitespace ?> checked="checked"<?cs /if ?> />
      <label for="whitespace">空格鍵</label>
     </div>
    </fieldset>
    <div class="buttons">
     <input type="submit" name="update" value="刷新" />
    </div>
   </div>
  </form>
  <dl id="overview">
   <dt class="property author">作者:</dt>
   <dd class="author"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(multiple changes)</em><?cs
    else ?><?cs var:wiki.author ?> <span class="ipnr">(IP: <?cs
     var:wiki.ipnr ?>)</span><?cs
    /if ?></dd>
   <dt class="property time">日期:</dt>
   <dd class="time"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(multiple changes)</em><?cs
    elif:wiki.time ?><?cs var:wiki.time ?> (<?cs var:wiki.time_delta ?> ago)<?cs
    else ?>--<?cs
    /if ?></dd>
   <dt class="property message">描述:</dt>
   <dd class="message"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(multiple changes)</em><?cs
    else ?><?cs var:wiki.comment ?><?cs /if ?></dd>
  </dl>
  <div class="diff">
   <div id="legend">
    <h3>Legend:</h3>
    <dl>
     <dt class="unmod"></dt><dd>沒有改變</dd>
     <dt class="add"></dt><dd>新增</dd>
     <dt class="rem"></dt><dd>刪除</dd>
     <dt class="mod"></dt><dd>修改</dd>
    </dl>
   </div>
   <ul class="entries">
    <li class="entry">
     <h2><?cs var:wiki.page_name ?></h2><?cs
      if:diff.style == 'sidebyside' ?>
      <table class="sidebyside" summary="Differences">
       <colgroup class="l"><col class="lineno" /><col class="content" /></colgroup>
       <colgroup class="r"><col class="lineno" /><col class="content" /></colgroup>
       <thead><tr>
        <th colspan="2">Version <?cs var:wiki.old_version ?></th>
        <th colspan="2">Version <?cs var:wiki.version ?></th>
       </tr></thead><?cs
       each:change = wiki.diff ?><?cs
        call:diff_display(change, diff.style) ?><?cs
       /each ?>
      </table><?cs
     else ?>
      <table class="inline" summary="Differences">
       <colgroup><col class="lineno" /><col class="lineno" /><col class="content" /></colgroup>
       <thead><tr>
        <th title="Version <?cs var:wiki.old_version ?>">v<?cs
          alt:wiki.old_version ?>0<?cs /alt ?></th>
        <th title="Version <?cs var:wiki.version ?>">v<?cs
          var:wiki.version ?></th>
        <th>&nbsp;</th>
       </tr></thead><?cs
       each:change = wiki.diff ?><?cs
        call:diff_display(change, diff.style) ?><?cs
       /each ?>
      </table><?cs
     /if ?>
    </li>
   </ul><?cs
   if:trac.acl.WIKI_DELETE &&
    (len(wiki.diff) == 0 || wiki.version == wiki.latest_version) ?>
    <form method="get" action="<?cs var:wiki.current_href ?>">
     <input type="hidden" name="action" value="delete" />
     <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
     <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" />
     <input type="submit" name="delete_version" value="刪除 <?cs
     if:wiki.version - wiki.old_version > 1 ?> 版本 <?cs
      var:wiki.old_version+1 ?> to <?cs
     /if ?>version <?cs var:wiki.version ?>" />
    </form><?cs
   /if ?>
  </div>

 <?cs elif wiki.action == "history" ?>
  <h1><a href="<?cs var:wiki.current_href ?>"><?cs
    var:wiki.page_name ?> 修改歷史</a></h1>
  <?cs if:len(wiki.history) ?><form class="printableform" method="get" action="">
   <input type="hidden" name="action" value="diff" />
   <div class="buttons">
    <input type="submit" value="查看修改" />
   </div>
   <table id="wikihist" class="listing" summary="Change history">
    <thead><tr>
     <th class="diff"></th>
     <th class="version">版本</th>
     <th class="date">日期</th>
     <th class="author">作者</th>
     <th class="comment">描述</th>
    </tr></thead>
    <tbody><?cs each:item = wiki.history ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="diff"><input type="radio" name="old_version" value="<?cs
        var:item.version ?>"<?cs
        if:name(item) == 1 ?> checked="checked"<?cs
        /if ?> /> <input type="radio" name="version" value="<?cs
        var:item.version ?>"<?cs
        if:name(item) == 0 ?> checked="checked"<?cs
        /if ?> /></td>
      <td class="version"><a href="<?cs
        var:item.url ?>" title="瀏覽此版本"><?cs
        var:item.version ?></a></td>
      <td class="date"><?cs var:item.time ?></td>
      <td class="author" title="IP-Address: <?cs var:item.ipaddr ?>"><?cs
        var:item.author ?></td>
      <td class="comment"><?cs var:item.comment ?></td>
     </tr>
    <?cs /each ?></tbody>
   </table><?cs
   if:len(wiki.history) > #10 ?>
    <div class="buttons">
     <input type="submit" value="查看修改" />
    </div><?cs
   /if ?>
  </form><?cs /if ?>

 <?cs else ?>
  <?cs if wiki.action == "edit" || wiki.action == "preview" || wiki.action == "collision" ?>
   <h1>正在編輯 "<?cs var:wiki.page_name ?>"</h1><?cs
    if wiki.action == "preview" ?>
     <table id="info" summary="Revision info"><tbody><tr>
       <th scope="col">
        Preview of future version <?cs var:$wiki.version+1 ?> (modified by <?cs var:wiki.author ?>)
       </th></tr><tr>
       <td class="message"><?cs var:wiki.comment_html ?></td>
      </tr>
     </tbody></table>
     <fieldset id="preview">
      <legend>Preview (<a href="#edit">skip</a>)</legend>
        <div class="wikipage"><?cs var:wiki.page_html ?></div>
     </fieldset><?cs
     elif wiki.action =="collision"?>
     <div class="system-message">
    對不起，本頁面在你編輯時已經有其它人同時修改了，所以你的修改不能被保存。
     </div><?cs
    /if ?>
   <form id="edit" action="<?cs var:wiki.current_href ?>" method="post">
    <fieldset class="iefix">
     <input type="hidden" name="action" value="edit" />
     <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
     <input type="hidden" id="scroll_bar_pos" name="scroll_bar_pos" value="<?cs
       var:wiki.scroll_bar_pos ?>" />
     <div id="rows">
      <label for="editrows">編輯區大小:</label>
      <select size="1" name="editrows" id="editrows" tabindex="43"
        onchange="resizeTextArea('text', this.options[selectedIndex].value)"><?cs
       loop:rows = 8, 42, 4 ?>
        <option value="<?cs var:rows ?>"<?cs
          if:rows == wiki.edit_rows ?> selected="selected"<?cs /if ?>><?cs
          var:rows ?></option><?cs
       /loop ?>
      </select>
     </div>
     <p><textarea id="text" class="wikitext" name="text" cols="80" rows="<?cs
       var:wiki.edit_rows ?>">
<?cs var:wiki.page_source ?></textarea></p>
     <script type="text/javascript">
       var scrollBarPos = document.getElementById("scroll_bar_pos");
       var text = document.getElementById("text");
       addEvent(window, "load", function() {
         if (scrollBarPos.value) text.scrollTop = scrollBarPos.value;
       });
       addEvent(text, "blur", function() { scrollBarPos.value = text.scrollTop });
     </script>
    </fieldset>
    <div id="help">
     <b>提示:</b>參考<a href="<?cs var:$trac.href.wiki
?>/ZhWikiFormatting">維基格式手冊</a> 及<a href="<?cs var:$trac.href.wiki
?>/ZhTracWiki">Trac維基</a> 獲得詳細幫助以編輯文章.
    </div>
    <fieldset id="changeinfo">
     <legend>修改註記</legend>
     <?cs if:trac.authname == "anonymous" ?>
      <div class="field">
       <label>請輸入使用者名稱或信箱地址:<br />
       <input id="author" type="text" name="author" size="30" value="<?cs
         var:wiki.author ?>" /></label>
      </div>
     <?cs /if ?>
     <div class="field">
      <label>最新版註釋(選填):<br />
      <input id="comment" type="text" name="comment" size="60" value="<?cs
        var:wiki.comment?>" /></label>
     </div><br />
     <?cs if trac.acl.WIKI_ADMIN ?>
      <div class="options">
       <label><input type="checkbox" name="readonly" id="readonly" <?cs
         if wiki.readonly == "1"?>checked="checked"<?cs /if ?> />
       唯讀 </label>
      </div>
     <?cs /if ?>
    </fieldset>
    <div class="buttons"><?cs
     if wiki.action == "collision" ?>
      <input type="submit" name="preview" value="瀏覽" disabled="disabled" />&nbsp;
      <input type="submit" name="save" value="送出" disabled="disabled" />&nbsp;
     <?cs else ?>
      <input type="submit" name="preview" value="瀏覽" accesskey="r" />&nbsp;
      <input type="submit" name="save" value="送出" />&nbsp;
     <?cs /if ?>
     <input type="submit" name="cancel" value="放棄" />
    </div>
    <script type="text/javascript" src="<?cs
      var:htdocs_location ?>js/wikitoolbar.js"></script>
   </form>
  <?cs /if ?>
  <?cs if wiki.action == "view" ?>
   <?cs if:wiki.comment_html ?>
    <table id="info" summary="Revision info"><tbody><tr>
      <th scope="col">
       Version <?cs var:wiki.version ?> (modified by <?cs var:wiki.author ?>, <?cs var:wiki.age ?> ago)
      </th></tr><tr>
      <td class="message"><?cs var:wiki.comment_html ?></td>
     </tr>
    </tbody></table>
   <?cs /if ?>
   <div class="wikipage">
    <div id="searchable"><?cs var:wiki.page_html ?></div>
   </div>
   <?cs if:len(wiki.attachments) ?>
    <h3 id="tkt-changes-hdr">附件</h3>
    <ul class="tkt-chg-list"><?cs
     each:attachment = wiki.attachments ?><li class="tkt-chg-change"><a href="<?cs
      var:attachment.href ?>"><?cs
      var:attachment.filename ?></a> (<?cs var:attachment.size ?>) -<?cs
      if:attachment.description ?><q><?cs var:attachment.description ?></q>,<?cs
      /if ?> added by <?cs var:attachment.author ?> on <?cs
      var:attachment.time ?>.</li><?cs
     /each ?>
    </ul>
  <?cs /if ?>
  <?cs if wiki.action == "view" && (trac.acl.WIKI_MODIFY || trac.acl.WIKI_DELETE)
      && (wiki.readonly == "0" || trac.acl.WIKI_ADMIN) ?>
   <div class="buttons"><?cs
    if:trac.acl.WIKI_MODIFY ?>
     <form method="get" action="<?cs var:wiki.current_href ?>"><div>
      <input type="hidden" name="action" value="edit" />
      <input type="submit" value="<?cs if:wiki.exists ?>編輯<?cs
        else ?>新增<?cs /if ?> 頁面" accesskey="e" />
     </div></form><?cs
     if:wiki.exists ?>
      <form method="get" action="<?cs var:wiki.attach_href ?>"><div>
       <input type="hidden" name="action" value="new" />
       <input type="submit" value="上傳附件" />
      </div></form><?cs
     /if ?><?cs
    /if ?><?cs
    if:wiki.exists && trac.acl.WIKI_DELETE ?>
     <form method="get" action="<?cs var:wiki.current_href ?>"><div id="delete">
      <input type="hidden" name="action" value="delete" />
      <input type="hidden" name="version" value="<?cs var:wiki.version ?>" /><?cs
      if:wiki.version == wiki.latest_version ?>
       <input type="submit" name="delete_version" value="刪除此版本" /><?cs
      /if ?>
      <input type="submit" value="刪除本頁" />
     </div></form>
    <?cs /if ?>
   </div>
  <?cs /if ?>
  <script type="text/javascript">
   addHeadingLinks(document.getElementById("searchable"), "Link to this section");
  </script>
 <?cs /if ?>
 <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
