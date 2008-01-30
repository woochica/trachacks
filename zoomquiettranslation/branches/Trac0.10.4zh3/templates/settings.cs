<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>配置与用户会话管理</h1>

 <h2>用户设置</h2>
 <p>
本页面功能:使用户自定义自己的Trac设置,会话设置是保存在服务器上和用户id以"会话索引"的形式保存在客户
端浏览器的cookie目录下.本cookies可使Trac重新获得用户的设置
 </p>
 <form method="post" action="">
 <div>
  <h3>个人信息</h3>
  <div>
   <input type="hidden" name="action" value="save" />
   <label for="name">名字:</label>
   <input type="text" id="name" name="name" class="textwidget" size="30"
          value="<?cs var:settings.name ?>" />
  </div>
  <div>
   <label for="email">邮箱地址:</label>
   <input type="text" id="email" name="email" class="textwidget" size="30"
          value="<?cs var:settings.email ?>" />
  </div><?cs
  if:settings.session_id ?>
   <h3>会话</h3>
   <div>
    <label for="newsid">会话索引:</label>
    <input type="text" id="newsid" name="newsid" class="textwidget" size="30"
           value="<?cs var:settings.session_id ?>" />
    <p>会话索引用于查找保存在服务器上的用户个人信息和会话的日期,默认情况下是自动生成,用户可以随时
    把它修改容易记忆的索引值保存到本地的非浏览器cookies目录</p>
   </div><?cs
  /if ?>
  <div>
   <br />
   <input type="submit" value="发送提交" />
  </div >
 </div>
</form><?cs
if:settings.session_id ?>
 <hr />
 <h2>上传会话索引</h2>
 <p>用户可以上传保存的会话索引,点击"恢复",可使你在不同的电脑或者浏览器上使用统一的设置.</p>
 <form method="post" action="">
  <div>
   <input type="hidden" name="action" value="load" />
   <label for="loadsid">本地会话索引:</label>
   <input type="text" id="loadsid" name="loadsid" class="textwidget" size="30"
          value="" />
   <input type="submit" value="恢复" />
  </div>
 </form><?cs
/if ?>

</div>
<?cs include:"footer.cs"?>
