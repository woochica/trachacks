<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Available Milestones</title></head>
<body>

<h2>传票: 传票视图</h2>


<form id="relaticketadmin" action="rtadmin" method="post">

  <div class="field">

  <table class="listing" id="millist">
   <thead>
    <tr><th class="sel">启用</th><th>里程碑</th>
    </tr>
   </thead><tbody><?cs
   each:milestone = milestones ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:milestone.name ?>" <?cs 
     if:milestone.enabled ?> checked="checked"<?cs
     /if ?> /></td>
    <td><?cs var:milestone.name ?></td>
   </tr><?cs
   /each ?></tbody>
  </table>
	
	<input type="submit" name="save" value="保存" accesskey="s" />  
  </div>
  
</form>

</html>
