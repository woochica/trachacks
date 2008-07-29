<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="attachment">

<?cs if:attachment.mode == 'new' ?>
 <h1>添加附件到<a href="<?cs var:attachment.parent.href?>"><?cs
   var:attachment.parent.name ?></a></h1>
 <form id="attachment" method="post" enctype="multipart/form-data" action="">
  <div class="field">
   <label>文件路径:<br /><input type="file" name="attachment" /></label>
  </div>
  <fieldset>
   <legend>附件信息</legend>
   <?cs if:trac.authname == "anonymous" ?>
    <div class="field">
     <label>用户名字或者邮箱地址:<br />
     <input type="text" name="author" size="30" value="<?cs
       var:attachment.author?>" /></label>
    </div>
   <?cs /if ?>
   <div class="field">
    <label>文件描述 (可选1):<br />
    <input type="text" name="description" size="60" /></label>
   </div>
   <br />
   <div class="options">
    <label><input type="checkbox" name="replace" />
    覆盖原有同名文件</label>
   </div>
   <br />
  </fieldset>
  <div class="buttons">
   <input type="hidden" name="action" value="new" />
   <input type="hidden" name="type" value="<?cs var:attachment.parent.type ?>" />
   <input type="hidden" name="id" value="<?cs var:attachment.parent.id ?>" />
   <input type="submit" value="添加附件" />
   <input type="submit" name="cancel" value="取消" />
  </div>
 </form>
<?cs elif:attachment.mode == 'delete' ?>
 <h1><a href="<?cs var:attachment.parent.href ?>"><?cs
   var:attachment.parent.name ?></a>: <?cs var:attachment.filename ?></h1>
 <p><strong>是否要删除此附件?</strong><br />
 This is an irreversible operation.</p>
 <div class="buttons">
  <form method="post" action=""><div id="delete">
   <input type="hidden" name="action" value="delete" />
   <input type="submit" name="cancel" value="取消" />
   <input type="submit" value="删除附件" />
  </div></form>
 </div>
<?cs elif:attachment.mode == 'list' ?>
 <h1><a href="<?cs var:attachment.parent.href ?>"><?cs
   var:attachment.parent.name ?></a></h1><?cs
  call:list_of_attachments(attachment.list, attachment.attach_href) ?>
<?cs else ?>
 <h1><a href="<?cs var:attachment.parent.href ?>"><?cs
   var:attachment.parent.name ?></a>: <?cs var:attachment.filename ?></h1>
 <table id="info" summary="Description"><tbody><tr>
   <th scope="col">
    File <?cs var:attachment.filename ?>, <?cs var:attachment.size ?> 
    (added by <?cs var:attachment.author ?>,  <?cs var:attachment.age ?> ago)
   </th></tr><tr>
   <td class="message"><?cs var:attachment.description ?></td>
  </tr>
 </tbody></table>
 <div id="preview"><?cs
  if:attachment.preview ?>
   <?cs var:attachment.preview ?><?cs
  elif:attachment.max_file_size_reached ?>
   <strong>HTML preview not available</strong>, since the file size exceeds
   <?cs var:attachment.max_file_size  ?> bytes. You may <a href="<?cs
     var:attachment.raw_href ?>">下载附件</a> instead.<?cs
  else ?>
   <strong>HTML preview not available</strong>. To view the file,
   <a href="<?cs var:attachment.raw_href ?>">download the file</a>.<?cs
  /if ?>
 </div>
 <?cs if:attachment.can_delete ?><div class="buttons">
  <form method="get" action=""><div id="delete">
   <input type="hidden" name="action" value="delete" />
   <input type="submit" value="删除附件" />
  </div></form>
 </div><?cs /if ?>
<?cs /if ?>

</div>
<?cs include "footer.cs"?>
