<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head>
 <title>Report Manager</title>
 <script type="text/javascript">
 {

	function onDeleteEntry(parentNode, event) { 
		parentNode.parentNode.parentNode.removeChild(parentNode.parentNode);
	}

	function onIdChange(src, event) { 
		sortById();
	}

	function sortById() { 
		reportlist = window.document.getElementById("reportlist");
	}

 }
 </script>

</head>
<body>

<h2>Edit History: #<?cs var:editHistoryId?>(<?cs var:reports_log?>)
</h2>


<form id="editreports" action="reportmanager" method="post">

  <div class="field">
	<label> History log: </label>
	<input type="text" name="reports_log" />
	<input type="submit" name="applyedit" value="Save" />
	<input type="submit" name="cancel" value="Cancel" />
	<input type="hidden" name="history_id" value="<?cs var:editHistoryId?>" />
  </div>

  <input type="reset" name="reset" value="Reset" />

  <table class="listing" id="reportlist">
   <thead>
    <tr>
	 <th>Id</th>
	 <th>New Id</th>
	 <th>Title</th>
	 <th>Delete</th>
	</tr>
   </thead><?cs each:report_entry = report_list ?>
    <tr>
     <td class="name">
	   <?cs var:report_entry.id ?>
     </td>

     <td class="name">
	   <input  size="3" type="text" onchange="onIdChange(this, event)" name="report_<?cs var:report_entry.id ?>"  
	     value="<?cs var:report_entry.id ?>" />
	 </td>

     <td class="name">
	   <?cs var:report_entry.title ?> 
	 </td>

	 <td class="name">
	  <input type="button"  onclick="onDeleteEntry(this.parentNode, event)" value="Delete" />
	 </td>

    </tr><?cs
   /each ?>
  </table>

  
</form>
</body>

</html>
