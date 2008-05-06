<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="changeset">
 <div id="title">
    <h1>選擇要比較的版號:</h1>
 </div>

 <div id="anydiff">
  <form action="<?cs var:anydiff.changeset_href ?>" method="get">
   <table>
    <tr>
     <th><label for="old_path">文件:</label></th>
     <td>
      <input type="text" id="old_path" name="old_path" value="<?cs
         var:anydiff.old_path ?>" size="44" />
      <label for="old_rev">版號:</label>
      <input type="text" id="old_rev" name="old" value="<?cs
         var:anydiff.old_rev ?>" size="4" />
     </td>
    </tr>
    <tr>
     <th><label for="new_path">文件:</label></th>
     <td>
      <input type="text" id="new_path" name="new_path" value="<?cs
         var:anydiff.new_path ?>" size="44" />
      <label for="new_rev">版號:</label>
      <input type="text" id="new_rev" name="new" value="<?cs
         var:anydiff.new_rev ?>" size="4" />
     </td>
    </tr>
   </table>
   <div class="buttons">
      <input type="submit" value="顯示修改" />
   </div>
  </form>
 </div>
 <div id="help">
  <strong>提示:</strong>查看<a href="<?cs var:trac.href.wiki
  ?>/ZhTracChangeset#ExaminingDifferencesBetweenBranches">變更集</a> 對本頁面的幫助.
 </div>
</div>

<?cs include "footer.cs"?>
