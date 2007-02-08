<h2>Configuration Problem</h2>

<fieldset>
<table >
<tr>
<td>
There appears to be a configuration problem for the testcaseplugin.  The reason could be one of the following:
<li>there are no testcases in subversion at the specified path</li>
<li>the trac.ini file is missing the config variable SubversionPathToTestCases under the section 'testcaseExtension'</li>
<li>the current user is not allowed to access the subversion repository using the current trac acount</li>
</td>
</tr>
</table>
<p>
Error message if any specified here : <?cs var:testcase.run.errormessage ?>
</p>

</fieldset>