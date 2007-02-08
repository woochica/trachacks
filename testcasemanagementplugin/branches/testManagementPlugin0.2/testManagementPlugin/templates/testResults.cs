    <h2>Track Test Case Results</h2>
    <fieldset>
    <form id="sprintMain" action="" method="post">
        <br/>
        <p>
            <label>Select sprint to report on:<br/></label>                 
                <select name="selectedmilestone" onchange="this.form.submit()">
                    <?cs each:mile_stone = sprint.milestones ?>
                        <option value="<?cs var:mile_stone.name ?>" <?cs
                            if: milestone.currentMilestone.name == mile_stone.name ?> selected="selected"<?cs
                            /if ?>><?cs var:mile_stone.name ?></option>
                    <?cs /each ?>
                </select>
            <noscript><input type="submit" value="updateMilestone" /></noscript>
        </p>
    </form>
</fieldset>
<fieldset>
            <li class="milestone">
                       <div class="info">
                            <h2>
                                Sprint: <em><?cs var:milestone.currentMilestone.name ?></em>
                           </h2>
                       <p>
                            <fieldset>
                                <legend>Description</legend>
                                <?cs var:milestone.currentMilestone.description ?>                    
                            </fieldset>
                       </p>
                           <?cs with:stats=milestone.currentMilestone.stats ?>
                        </p>
                            <table>
                                <tr>
                                    <td>
                                        <fieldset>
                                        <legend>Total Tests Completed</legend>
                                        <table class="progress" >
                                           <tr>
                                                <td class="closed" style="width: <?cs
                                                  var:#stats.percent_closed ?>%"><a href="<?cs
                                                  var:milestone.currentMilestone.queries.closed_tickets ?>" title="<?cs
                                                  var:#stats.closed_tickets ?> of <?cs
                                                  var:#stats.total_tickets ?> ticket<?cs
                                                  if:#stats.total_tickets != #1 ?>s<?cs /if ?> closed"></a></td>
                                                <td class="open" style="width: <?cs
                                                  var:#stats.percent_active ?>%"><a href="<?cs
                                                  var:milestone.currentMilestone.queries.active_tickets ?>" title="<?cs
                                                  var:#stats.active_tickets ?> of <?cs
                                                  var:#stats.total_tickets ?> ticket<?cs
                                                  if:#stats.total_tickets != #1 ?>s<?cs /if ?> active"></a></td>
                                            </tr>
                                        </table>
                                        <br/>
                                        <p class="percent"><?cs var:#stats.percent_closed ?>%</p>
                                        <dl>
                                        <dt>Closed tickets:</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.closed_tickets ?>"><?cs
                                        var:stats.closed_tickets ?></a></dd>
                                        <dt>Active tickets:</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.active_tickets ?>"><?cs
                                        var:stats.active_tickets ?></a></dd>
                                        </dl>
                                        </fieldset>
                                    </td>
                                </tr>
                                <tr>
                                    <td>  
                                        <fieldset>
                                        <legend>Percent tickets passed</legend>
                                        <table class="progress" >
                                           <tr>
                                                <td class="closed" style="width: <?cs
                                                  var:#stats.percent_time_closed ?>%"><a href="<?cs
                                                  var:milestone.currentMilestone.queries.closed_tickets ?>" title="<?cs
                                                  var:#stats.closed_tickets ?> of <?cs
                                                  var:#stats.total_tickets ?> ticket<?cs
                                                  if:#stats.total_tickets != #1 ?>s<?cs /if ?> closed"></a></td>
                                                <td class="open" style="width: <?cs
                                                  var:#stats.percent_time_active ?>%"><a href="<?cs
                                                  var:milestone.currentMilestone.queries.active_tickets ?>" title="<?cs
                                                  var:#stats.active_tickets ?> of <?cs
                                                  var:#stats.total_tickets ?> ticket<?cs
                                                  if:#stats.total_tickets != #1 ?>s<?cs /if ?> active"></a></td>
                                            </tr>
                                        </table>
                                        <br/>
                                        <p class="percent"><?cs var:#stats.percent_time_closed ?>%</p>
                                        <dl>
                                        <dt>Closed tickets:</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.closed_tickets  ?>"><?cs
                                        var:stats.closed_tickets ?></a></dd>
                                        <dt>Active tickets with time estimates:</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.active_tickets_with_time ?>"><?cs
                                        var:stats.active_tickets_with_time ?></a>
                                        <dt>Open Tickets with no time estimates:</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.active_tickets_no_time ?>"><?cs
                                        var:stats.active_tickets_no_time ?></a>
                                        <br/>
                                        <br/>
                                        <dt>Closed Tickets with no time (estimated or actual):</dt>
                                        <dd><a href="<?cs var:milestone.currentMilestone.queries.closed_tickets_no_time ?>"><?cs
                                        var:stats.closed_tickets_with_no_time ?></a>
                                        <br/>
                                        </fieldset>
                                    </td>
                                </tr>
                            </table>
                        <?cs /with ?>
                       </div>
                       <div class="description"><?cs var:milestone.description ?></div>
                      </li>
                </ul>
                <p>
                    <fieldset>
                    <br><b>Test Case Results</b></br>
                    <table size="80%" cellpadding="4" cellspacing="3" border="1">
                        <th>Name</th><th>Total Tickets</th><th>Open Test Cases</th><th>Closed Test Cases</th><th>Tests Passed</th><th>Tests Failed</th><th>Tests Incomplete</th>
                        <?cs with:owners=milestone.currentMilestone.owners ?>
                            <?cs each:owner = owners ?>
                                <tr align="center">
                                    <td>
                                        <?cs var:owner.name ?>
                                    </td>
                                    <td>
                                        <a href="query?milestone=<?cs var:milestone.currentMilestone.name?>&owner=<?cs var:owner.name?>&order=priority">
                                            <?cs var:owner.totaltickets ?>
                                        </a>                                        
                                    </td>
                                    <td>
                                        <a href="query?status=new&status=assigned&status=reopened&time_estimate=%21&milestone=<?cs var:milestone.currentMilestone.name?>&owner=<?cs var:owner.name?>&order=priority">
                                            <?cs var:owner.ticketsopenwithtime ?>
                                        </a>
                                    </td>
                                    <td>
                                        <a href="query?status=new&status=assigned&status=reopened&milestone=<?cs var:milestone.currentMilestone.name?>&time_estimate=&owner=<?cs var:owner.name?>&order=priority&order=status">
                                           <?cs var:owner.ticketsopenwithnotime ?>
                                        </a>
                                    </td>
                                    <td>
                                        <a href="query?status=closed&milestone=<?cs var:milestone.currentMilestone.name?>&owner=<?cs var:owner.name?>&order=priority">
                                            <?cs var:owner.closedtickets ?>
                                        </a>
                                    </td>
                                    <td>
                                        <?cs var:owner.daysleft ?>
                                    </td>
                                    <td>
                                        <?cs var:owner.dayscompleted ?>
                                    </td>
                                </tr>
                            <?cs /each ?>
                        <?cs /with ?>
                    </table>                       
                    </fieldset>
                </p>
                <p>
                    <fieldset>
                    <br><b>Summary</b></br>
                    <table cellpadding="4" cellspacing="3" border="0" >
                        <th>Resources</th><th>Total Tickets</th><th>Open Test Cases</th><th>Closed Test Cases</th><th>Tests Passed</th><th>Tests Failed</th><th>Tests Incomplete</th>
                        <?cs with:summary=milestone.currentMilestone.summary ?>                      
                            <tr align="center" >
                                <td>
                                    <?cs var:summary.resources ?>
                                </td>
                                <td>
                                    <a href="query?milestone=<?cs var:milestone.currentMilestone.name?>&order=priority">
                                        <?cs var:summary.totaltickets ?>
                                    </a>
                                </td>
                                <td>
                                    <a href="query?status=new&status=assigned&status=reopened&time_estimate=%21&milestone=<?cs var:milestone.currentMilestone.name?>&order=priority">
                                        <?cs var:summary.ticketsopenwithtime ?>
                                    </a>
                                </td>
                                <td>
                                    <a href="query?status=new&status=assigned&status=reopened&milestone=<?cs var:milestone.currentMilestone.name?>&time_estimate=&order=priority">
                                        <?cs var:summary.ticketsopenwithnotime ?>
                                    </a>
                                </td>
                                <td>
                                    <a href="query?status=closed&milestone=<?cs var:milestone.currentMilestone.name?>&order=priority">
                                        <?cs var:summary.totalticketsclosed ?>
                                    </a>
                                </td>
                                <td>
                                    <?cs var:summary.workleft ?>
                                </td>
                                <td>
                                    <?cs var:summary.workcompleted ?>
                                </td>
                            </tr>
                        <?cs /with ?>
                    </table>
                    </fieldset>
                   </p>
                 </fieldset>
         </fieldset>
    </form>

     
