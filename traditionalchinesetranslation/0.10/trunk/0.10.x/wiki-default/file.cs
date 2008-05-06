<?cs set:html.stylesheet = 'css/browser.css' ?>
<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <?cs if:args.mode != 'attachment' && trac.acl.LOG_VIEW ?><ul>
  <li class="last"><a href="<?cs var:file.logurl ?>">修訂紀錄</a></li>
 </ul><?cs /if ?>
</div>

<div id="content" class="file">

 <?cs if file.attachment_parent ?>
  <h1><a href="<?cs var:file.attachment_parent_href ?>"><?cs
    var:file.attachment_parent ?></a>: <?cs var:file.filename ?></h1>

 <?cs else ?>
  <?cs call:browser_path_links(file.path, file) ?>
  <div id="jumprev">
   <form action="" method="get">
    <div>
     <label for="rev">檢閱修訂版號：</label>
     <input type="text" id="rev" name="rev" value="<?cs
       var:file.rev ?>" size="4" />
    </div>
   </form>
  </div>
  <table id="info" summary="修訂資訊">
   <tr>
    <th scope="row">
     修訂版號 <a href="<?cs var:file.chgset_href ?>"><?cs var:file.rev ?></a>
     (by <?cs var:file.rev_author ?>, <?cs var:file.rev_date ?>)
    </th>
    <td class="message"><?cs var:file.rev_msg ?></td>
   </tr>
  </table>
 <?cs /if ?>

 <div id="preview">
  <?cs if:file.highlighted_html ?>
   <?cs var:file.highlighted_html ?>
  <?cs elif:file.max_file_size_reached ?>
   <strong>無法 HTML 預覽</strong>，檔案大小超過
   <?cs var:file.max_file_size  ?> bytes。
   Try <a href="?format=raw">downloading the file</a> instead.
  <?cs else ?>
   <strong>無法 HTML 預覽</strong>。請 <a href="<?cs
   var:file.filename + '?rev=' + file.rev ?>&format=raw">下載檔案</a> 檢閱。
  <?cs /if ?>
 </div>

 <?cs if:attachment.delete_href ?><div class="buttons">
  <form method="get" action=""><div id="delete">
   <input type="hidden" name="delete" value="yes" />
    <input type="submit" value="Delete Attachment" onclick="return confirm('Do you really want to delete this attachment?\nThis is an irreversible operation.')" />
  </div></form>
 </div><?cs /if ?>

 <?cs if:!file.attachment_parent ?>
  <div id="help">
   <strong>註：</strong> 請參閱 <a href="<?cs var:trac.href.wiki
   ?>/TracBrowser">TracBrowser</a> 的操作說明
  </div>
 <?cs /if ?>


</div>

<?cs include "footer.cs"?>
