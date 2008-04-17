<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Available Projects</title></head>
<body>

<h2>模板: <?cs var:tt_name?>
</h2>



<form id="savetickettemplate" action="tickettemplate" method="post">

  <table class="listing" id="configlist">
   <thead>
    <tr>
	 <th>模板历史</th>
	</tr>
   </thead><?cs each:history = tt_history ?>
    <tr>
     <td class="name"><a href="<?cs var:history.href?>"><?cs
       var:history.modi_time ?></a></td>
    </tr><?cs
   /each ?>
  </table>
  
</form>



</html>
