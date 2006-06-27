<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="burndown">
 <h1>Burndown Chart</h1>
</div>

<form action="<?cs var:burndown.href ?>" method="post">
    <label for="selected_milestone">Select milestone:</label>
    <select id="selected_milestone" name="selected_milestone">
        <?cs each:mile = milestones ?>
            <option value="<?cs var:mile ?>" <?cs if:selected_milestone == mile ?> selected="selected"<?cs /if ?> >
                <?cs var:mile ?>
            </option>
        <?cs /each ?>
    </select>
    <label for="selected_component">Select component:</label>
    <select id="selected_component" name="selected_component">
        <option>All Components</option>
        <?cs each:comp = components ?>
            <option value="<?cs var:comp ?>" <?cs if:selected_component == comp ?> selected="selected"<?cs /if ?> >
                <?cs var:comp ?>
            </option>
        <?cs /each ?>
    </select>

    <div class="buttons">
        <?cs if:start_complete ?>
            <input type="submit" name="start" value="Start Milestone" />
            <input type="submit" name="complete" value="Milestone Complete" />
        <?cs /if ?>
        <input type="submit" value="Show Burndown Chart" />
    </div>
</form>

<br />

<?cs if:draw_graph ?>
    
    <b>Current effort remaining: <?cs var:burndown_data[len(burndown_data) - 1][1] ?> hours</b>
    <br/>
    <br/>
    
<!-- graph code begins here-->
<script src="/cgi-bin/trac.cgi/chrome/hw/js/line.js" type="text/javascript"></script>
<script src="/cgi-bin/trac.cgi/chrome/hw/js/wz_jsgraphics.js" type="text/javascript"></script>

<div id="myCanvas" style="overflow: auto; position:relative;height:400px;width:800px;"></div>

<script>
    var g = new line_graph();
    
    <?cs each:tuple = burndown_data ?>
        g.add('<?cs var:tuple[0] ?>', <?cs var:tuple[1] ?>);
    <?cs /each ?>

    /*
    g.add('1', 1200);
    g.add('2', 1140);
    g.add('3', 1107);
    g.add('4', 1045);
    g.add('5', 900);
    g.add('6', 928);
    g.add('7', 887);
    g.add('8', 850);
    g.add('9', 924);
    g.add('10', 880);
    g.add('11', 809);
    g.add('12', 670);
    g.add('13', 612);
    g.add('14', 546);
    g.add('15', 500);
    g.add('16', 541);
    g.add('17', 508);
    g.add('18', 432);
    g.add('19', 500);
    g.add('20', 412);
    g.add('21', 360);
    g.add('22', 300);
    g.add('23', 215);
    g.add('24', 205);
    g.add('25', 246);
    g.add('26', 180);
    g.add('27', 110);
    g.add('28', 90);
    g.add('29', 40);
    g.add('30', 0);
    */
    
    //If called without a height parameter, defaults to 250
    g.render("myCanvas", "hours remaining vs. days of sprint", 300);

</script>
<!-- graph code ends here-->
<?cs /if ?>

<?cs include "footer.cs" ?>
