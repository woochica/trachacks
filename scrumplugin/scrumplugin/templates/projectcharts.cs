<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<h1>Project charts</h1>

<form action="<?cs var:projectcharts.href ?>" method="post">
  <label for="selected_milestone">Milestone:</label>
  <select id="selected_milestone" name="selected_milestone">
    <?cs each:milestone = milestones ?>
      <option value="<?cs var:milestone ?>" <?cs if:selected_milestone == milestone ?> selected="selected"<?cs /if ?> >
        <?cs var:milestone ?>
      </option>
    <?cs /each ?>
  </select>
  <?cs if:start_complete ?>
    <input type="submit" name="start" value="Start Milestone" />
    <input type="submit" name="complete" value="End Milestone" />
  <?cs /if ?>
  <input type="submit" value="Show Chart"/>
</form>

<applet id="chartApplet" width="100%" height="600"
  codebase= "chrome/hw" code="ProjectCharts.class"
  archive="jfreechart-1.0.3.jar,jcommon-1.0.6.jar" mayscript="true">
  <param name=mayscript value="true" >
</applet>

<script language="JavaScript" type="text/javascript">
  var chartApplet = document.chartApplet;
 
  chartApplet.markTimePeriod(<?cs var:milestone.begin ?>, <?cs var:milestone.end ?>, '<?cs var:selected_milestone ?>');
  chartApplet.chart.getTitle().setText('<?cs var:selected_milestone ?>');
    
  <?cs each:dataset = datasets ?>
    <?cs each:point = dataset ?>
      chartApplet.addTracTimePoint(<?cs var:point[0] ?>, <?cs var:point[1] ?>, '<?cs name:dataset ?>');
    <?cs /each ?>
  <?cs /each ?>
</script>

<?cs include "footer.cs" ?>
