
    <h2>Manage Test Run</h2>
    <form class="mod" id="orgTemp" method="post">
         <fieldset>
            <legend>Create new test run</legend>
            <div id="createNewRun">
                <fieldset>
                    <label>
                        The current testcase path location is: <input type="text" name="pathConfiguration" size="60" value="<?cs var:testcase.run.pathConfiguration ?>" readonly="true" /> 
                        <br/>To Validate the test configuration for the tests in the above location click the following link: <a href="<?cs var:testcase.run.validatePath ?>">Validate Link</a>
                    </label>        
                </fieldset>
                <table>
                    <tr>
                        <td>   
                            <fieldset>
                                <label>Enter a test configuration keyword.  This keyword can be used to differentiate between test runs.  An example would be internal versus an external client test configuration.  This is not a required field</label><br/>
                                <input type="text" name="testconfiguration"/>
                                <br/>
                            </fieldset>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <fieldset>
                                <legend>REQUIRED FIELD</legend>
                                <label><b>Select users to generate tickets for:</b></label><br/>                    
                                    <select name="users" cols="10" MULTIPLE size="10">
                                         <?cs each:user = testcase.run.users ?>
                                             <option value="<?cs var:user ?>"><?cs var:user ?></option>
                                        <?cs /each ?>
                                    </select>
                            </fieldset>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <fieldset>
                                <legend>Select Appropriate Version and or Milestone</legend>
                                <table cellspacing="4" cellpadding="4">
                                    <th><b>Version</b></th><th><b>Milestone/Sprint</b></th>
                                    <tr>
                                        <td>    
                                            <select name="selectedversion">
                                                <?cs each:version = testcase.run.versions ?>
                                                    <option value="<?cs var:version ?>" <?cs if: version == "" ?> selected="selected"<?cs
                                                        /if ?>><?cs var:version ?></option>
                                                <?cs /each ?>                                                                               
                                            </select>
                                        </td>
                                        <td>    
                                            <select name="selectedmilestone" >
                                                <?cs each:sprint = testcase.run.sprints ?>
                                                    <option value="<?cs var:sprint ?>" <?cs
                                                        if: sprint == "" ?> selected="selected"<?cs
                                                        /if ?>><?cs var:sprint ?></option>
                                                <?cs /each ?>
                                            </select>
                                        </td>
                                    </tr>
                                </table>
                            </fieldset>
                        </td> 
                    </tr>
                    <tr>
                        <td>
                            <table cellpadding="3" cellspacing="3" border="1">
                                <th>Select Templates</th>
                                <th>Select Additional Tests</th>
                                <tr>
                                    <td>
                                        <select name="testtemplates" cols="10" MULTIPLE size="10">
                                            <?cs each:template = testcase.run.testtemplates ?>
                                                <option value="<?cs var:template ?>"><?cs var:template ?></option>
                                            <?cs /each ?>
                                        </select>
                                    </td>
                                    <td>
                                        <select name="testcases" cols="10" MULTIPLE size="10">
                                            <?cs each:test = testcase.run.testcases ?>
                                                <option value="<?cs var:test ?>"><?cs var:test ?></option>
                                            <?cs /each ?>
                                        </select>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>            
            <div class="buttons">
                <input type="submit" name="GenerateTestRun" value="Generate Test Run"/> 
            </div>
        </fieldset>
    </form>
