<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="burndown">
<table cellpadding="0" cellspacing="0" border="0">
<tr><td><img src="<?cs var:chrome.href ?>/hw/images/trac-scrum-burndown-plugin-logo.png" /></td>
<td><h1 style="left: 20px; position: relative;">Burndown Chart</h1></td>
</tr></table>
<br/>

<form action="<?cs var:burndown.href ?>" method="get">
    <label for="selected_milestone">Select milestone:</label>
    <select id="selected_milestone" name="selected_milestone">
        <?cs each:mile = milestones ?>
            <option value="<?cs var:mile['name'] ?>" <?cs if:selected_milestone['name'] == mile['name'] ?> selected="selected"<?cs /if ?> >
                <?cs var:mile['name'] ?>
            </option>
        <?cs /each ?>
    </select>
    <label for="selected_component">Select component:</label>
    <select id="selected_component" name="selected_component">
        <option>All Components</option>
        <?cs each:comp = components ?>
            <option value="<?cs var:comp['name'] ?>" <?cs if:selected_component == comp['name'] ?> selected="selected"<?cs /if ?> >
                <?cs var:comp['name'] ?>
            </option>
        <?cs /each ?>
    </select>

    <div class="buttons">
        <?cs if:start ?>
            <input type="submit" name="start" value="Start Milestone" />
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
<script type="text/javascript" src="<?cs var:chrome.href ?>/hw/js/line.js"></script>
<script type="text/javascript" src="<?cs var:chrome.href ?>/hw/js/wz_jsgraphics.js"></script>
<div id="myCanvas" style="overflow: auto; position:relative;height:400px;width:800px;"></div>

<script>
    var g = new line_graph();
    
    <?cs each:tuple = burndown_data ?>
        g.add('<?cs var:tuple[0] ?>', <?cs var:tuple[1] ?>);
    <?cs /each ?>
    
    //If called without a height parameter, defaults to 250
    g.render("myCanvas", "hours remaining vs. days of sprint", 300);

</script>
<!-- graph code ends here-->
<?cs /if ?>

</div>
<?cs include "footer.cs" ?>
