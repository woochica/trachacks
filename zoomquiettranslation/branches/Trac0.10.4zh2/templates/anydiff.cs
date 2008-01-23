<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="changeset">
 <div id="title">
    <h1>选择要比较的底版本与高版本:</h1>
 </div>

 <div id="anydiff">
  <form action="<?cs var:anydiff.changeset_href ?>" method="get">
   <table>
    <tr>
     <th><label for="old_path">文件:</label></th>
     <td>
      <input type="text" id="old_path" name="old_path" value="<?cs
         var:anydiff.old_path ?>" size="44" />
      <label for="old_rev">版本号:</label>
      <input type="text" id="old_rev" name="old" value="<?cs
         var:anydiff.old_rev ?>" size="4" />
     </td>
    </tr>
    <tr>
     <th><label for="new_path">文件:</label></th>
     <td>
      <input type="text" id="new_path" name="new_path" value="<?cs
         var:anydiff.new_path ?>" size="44" />
      <label for="new_rev">版本号:</label>
      <input type="text" id="new_rev" name="new" value="<?cs
         var:anydiff.new_rev ?>" size="4" />
     </td>
    </tr>
   </table>
   <div class="buttons">
      <input type="submit" value="显示修改" />
   </div>
  </form>
 </div>
 <div id="help">
  <strong>提示:</strong>查看<a href="<?cs var:trac.href.wiki
  ?>/ZhTracChangeset#ExaminingDifferencesBetweenBranches">变更集</a> 对本页面的帮助.
 </div>
</div>

<?cs include "footer.cs"?>
