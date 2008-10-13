<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Report Manager</title></head>
<body>

<h2>Report History</h2>



<form id="save_histroy" class="addnew" action="reportmanager" method="post">

	<fieldset>
	<legend>Save history:</legend>
	  <div class="field">
		<label> History log: </label>
		<input type="text" name="reports_log" />
		<input type="submit" name="savereport" value="Save" />
	  </div>
	</fieldset>
</form>

<form id="reportmanager" action="reportmanager" method="post">

  <table class="listing" id="reportslist" >
   <thead>
    <tr>
	 <th> Id </th>
	 <th> History time </th>
	 <th> History log </th>
	 <th> Delete </th>
	 <th> Load </th>
	</tr>
   </thead><?cs each:history = report_history ?>
    <tr>
     <td class="name"><?cs var:history.id?></td>

     <td class="name"><?cs var:history.save_time?></td>

     <td class="name">
	   <a href="<?cs var:history.href?>?edit_<?cs var:history.id?>" >
	     <?cs var:history.reports_log?>
	   </a>
	 </td>

     <td class="name"><input type="submit" name="del_<?cs var:history.id ?>" value="Delete" /></td>

     <td class="name"><input type="submit" name="load_<?cs var:history.id ?>" value="Load" /></td>

    </tr><?cs
   /each ?>
  </table>

  
</form>

</body>

</html>
