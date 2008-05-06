<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>設定與用戶會話管理</h1>

 <h2>個人化設定</h2>
 <p>
本頁面功能:使用者可以自定Trac設定選項,會話設置是保存在服務器上和用戶id以"會話索引"的形式保存在客戶
端瀏覽器的cookie目錄下.本cookies可使Trac重新獲得用戶的設置
 </p>
 <form method="post" action="">
 <div>
  <h3>個人訊息</h3>
  <div>
   <input type="hidden" name="action" value="save" />
   <label for="name">名字:</label>
   <input type="text" id="name" name="name" class="textwidget" size="30"
          value="<?cs var:settings.name ?>" />
  </div>
  <div>
   <label for="email">電子郵件位址:</label>
   <input type="text" id="email" name="email" class="textwidget" size="30"
          value="<?cs var:settings.email ?>" />
  </div><?cs
  if:settings.session_id ?>
   <h3>會話</h3>
   <div>
    <label for="newsid">索引:</label>
    <input type="text" id="newsid" name="newsid" class="textwidget" size="30"
           value="<?cs var:settings.session_id ?>" />
    <p>會話索引用於查找保存在服務器上的用戶個人訊息和會話的日期,默認情況下是自動生成,用戶可以隨時
    把它修改容易記憶的索引值保存到本地的非瀏覽器cookies目錄</p>
   </div><?cs
  /if ?>
  <div>
   <br />
   <input type="submit" value="發送送出" />
  </div >
 </div>
</form><?cs
if:settings.session_id ?>
 <hr />
 <h2>上傳會話索引</h2>
 <p>用戶可以上傳保存的會話索引,點擊"恢復",可使你在不同的電腦或者瀏覽器上使用統一的設置.</p>
 <form method="post" action="">
  <div>
   <input type="hidden" name="action" value="load" />
   <label for="loadsid">本地會話索引:</label>
   <input type="text" id="loadsid" name="loadsid" class="textwidget" size="30"
          value="" />
   <input type="submit" value="恢復" />
  </div>
 </form><?cs
/if ?>

</div>
<?cs include:"footer.cs"?>
