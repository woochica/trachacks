<h2>Configuration Problem</h2>

<fieldset>
<table >
<tr>
<td>
There appears to be a configuration problem for the testcaseplugin.  The reason could be one of the following:
<li>there are no testcases in subversion at the specified path</li>
<li>the trac.ini file is missing the config variable SubversionPathToTestCases under the section 'testManagementExtension'</li>
<li>the current user is not allowed to access the subversion repository using the current trac acount</li>
<li>there is a problem with a test case or the testtemplates.xml file...check the errors below</li>
<li>do you have a testtemplates.xml file in the directory with your testcases?</li>
</td>
</tr>
</table>
<p>
Error message if any specified here : 
<table>
<?cs each:error_msg = testcase.run.errormessage  ?>
                <tr>
                    <td>
                        <?cs var:error_msg ?>
                    </td>
                </tr>
<?cs /each ?>    
<?cs var:testcase.run.errormessage ?>
</table>
</p>

<p>
<a href="<?cs var:testcase.run.urlPath ?>"> Click here to go back</a> to create a testrun for the path <b><?cs var:testcase.run.pathConfiguration ?></b>
</p>

</fieldset>