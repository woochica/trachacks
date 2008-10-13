<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>


<div id="datnav" class="nav">
    <ul>
        <li class="first">
        ← <a href="<?cs var:milestone ?>?date=<?cs var:prev_date ?>">Prev</a>
        </li>

        <li class="last">
        <a href="<?cs var:milestone ?>?date=<?cs var:next_date ?>">Next</a> →
        </li>
    </ul>

    <ul>
        <li>
		<form id="go" action="<?cs var:milestone ?>" method="post">
         <input type="text" name="go_date" value="<?cs var:cur_date_str ?>" size="10"/>
         <input type="submit" name="go" value="go" />
		</form>
        </li>
    </ul>

</div>

<div id="content" class="keylist">
    <h1 style="text-align:center;"><?cs var:milestone ?> : <?cs var:cur_date_str ?></h1>

    <div class="list1" id="item2">
        <img src="../burndown/<?cs var:milestone ?>/<?cs var:cur_date ?>.png" />
    </div>


    <div class="list1" id="item1" style="display: block;">
    <table id="relaTickets"  style="width: 880px;">
    <tbody>
        <tr>
            <td style="vertical-align: top;">
                <table class="wiki" id="relaTickets"  style="width: 660px;">
					<?cs if:enable_relaticket ?>
                    <thead>
                        <tr style="background-color:green;">
                            <th colspan="4">Relative Tickets</th>
                        </tr>
                        <tr style="background-color:#FFEFFF;">
                            <th style="width:200px; ">New</th>
                            <th style="width:200px; ">Doing</th>
                            <th style="width:200px; ">Done</th>
                        </tr>
                    </thead>

                    <tbody><?cs 
                        each:relarow = reladata ?>
                        <tr valign="top">
                            <td>
                                <a href="../../ticket/<?cs var:relarow.parent.id ?>" >#<?cs var:relarow.parent.id ?>::<?cs var:relarow.parent.summary ?></a><?cs 
                                each:item = relarow.new ?><p >
                                <a href="../../ticket/<?cs var:item.id ?>" > ~#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                                /each ?>
                            </td>

                            <td><?cs 
                                each:item = relarow.doing ?>
                                <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                                /each ?>
                            </td>

                            <td><?cs 
                                each:item = relarow.done ?>
                                <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                                /each ?>
                            </td>

                        </tr> <?cs 
                        /each ?>

                    </tbody>
					<?cs /if ?>

                    <thead>
                    <tr style="background-color:green;">
                        <th colspan="4">Summary</th>
                    </tr>
                    <tr style="background-color:#FFEFFF;">
                        <th style="width:200px; ">New</th>
                        <th style="width:200px; ">Doing</th>
                        <th style="width:200px; ">Done</th>
                    </tr>
                    </thead>

                    <tbody>
                    <tr valign="top">

                        <td><?cs 
                            each:item = puredata.purenew ?>
                            <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                            /each ?> <?cs  
							each:relarow = reladata ?>
                                <a href="../../ticket/<?cs var:relarow.parent.id ?>" >#<?cs var:relarow.parent.id ?>::<?cs var:relarow.parent.summary ?></a><p > <?cs
							/each ?>

                        </td>

                        <td><?cs 
                            each:item = puredata.puredoing ?>
                            <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                            /each ?>
                        </td>

                        <td><?cs 
                            each:item = puredata.puredone ?>
                            <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                            /each ?>
                        </td>


                    </tr>
                    
                    </tbody>
                </table>

            </td>
            <td style="vertical-align: top;">
			<?cs if:enable_unplanned ?>
                <table class="wiki" id="unplanned"  style="width: 220px;">
                    <thead>
                        <tr style="background-color:green;">
                            <th colspan="4">&nbsp;</th>
                        </tr>
                    <tr style="background-color:#FFEFFF;">
                        <th style="width:200px; ">Unplanned</th>
                    </tr>
                    </thead>

                    <tbody>
                        <tr valign="top">
                            <td><?cs 
                                each:item = unplanneddata ?>
                                <a href="../../ticket/<?cs var:item.id ?>" >#<?cs var:item.id ?>::<?cs var:item.summary ?></a><p><?cs
                                /each ?>
                            </td>

                        </tr>
                    </tbody>
                </table>
			<?cs /if ?>
            </td>
        </tr>
    </tbody>
    </table>

    </div>


    <div class="list1" id="item4">
        <img src="../date/<?cs var:milestone ?>/<?cs var:cur_date ?>.png" />
    </div> 

</div>

<?cs include "footer.cs"?>



