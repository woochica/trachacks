
    <h2>Enter the path to the location of the testcases in a branch</h2>
    
    <form class="mod" id="orgTemp" method="post">
         <fieldset>
            <legend>Set Temporary path to Testcase location </legend>
            <div id="createNewRun">
                <table>
                    <tr>
                        <td>   
                            <fieldset>
                                <p>Enter the path to the testcases in the branch in the format /branches/projectName/testcases</p>
                                <br/>
                                <p>Subversion is case sensative so make sure the path is correct...</p>
                                <br/>
                                <input type="text" name="pathConfiguration" size="60" value=<?cs var:testcases.path.path ?> />
                                <br/>
                                <br/>
                                <p>
                                Note changing the path here doesn't change the default location in the trac.conf configuration file.
                                </p>
                                <br/>
                            </fieldset>
                        </td>
                    </tr>
                </table>
            <div class="buttons">
                <input type="submit" name="setbranchlocation" value="Set Branch Location">
            </div>
        </fieldset>
    </form>
