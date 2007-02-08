<h2>Created Test Run</h2>

<fieldset>
<table border="1">
<tr>
<td>
Selected users for test run were:
<br/>    
<?cs each:user = testcase.run.selectedusers ?>
<li><?cs var:user ?></li><?cs /each ?>
</td>
</tr>
<tr>
<td>
Selected Test cases were :
<br/>
<?cs each:test = testcase.run.selectedtestcases ?>
<li><?cs var:test ?></li><?cs /each ?>
</td>
</tr>
</table>
<h2>Click <a href="<?cs var:testcase.run.basepath ?>/query?status=new&status=assigned&status=reopened&testcase_result=&type=testcase&order=priority">HERE</a> to see created test cases

</fieldset>
    
    
