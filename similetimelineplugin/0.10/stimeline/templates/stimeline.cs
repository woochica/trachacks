<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="timeline">
<h1>Timeline</h1>

<form id="prefs" method="get" action="<?cs var:stimeline.href ?>">
 <div>
  <label>View changes from <input type="text" size="10" name="from" value="<?cs
    var:timeline.from ?>" /></label> and
  <label><input type="text" size="3" name="daysback" value="<?cs
    var:timeline.daysback ?>" /> days back</label>.
 </div>
 <fieldset><?cs
  each:filter = timeline.filters ?>
   <label><input type="checkbox" name="<?cs var:filter.name ?>"<?cs
     if:filter.enabled ?> checked="checked"<?cs /if ?> /> <?cs
     var:filter.label ?></label><?cs
  /each ?>
 </fieldset>
 <div class="buttons">
  <input type="submit" name="update" value="Update" />
 </div>
</form>

<div id="trac-timeline" style="height: 500px; border: 1px solid #aaa"></div>
<script type="text/javascript">
/*
var tl;
function mk_timeline() {
  var eventSource = new Timeline.DefaultEventSource();
  var bandInfos = [
    Timeline.createBandInfo({
        eventSource:    eventSource,
        date:           "Jul 28 2006 00:00:00 GMT",
        width:          "20%", 
        intervalUnit:   Timeline.DateTime.WEEK, 
        intervalPixels: 100
    }),
    Timeline.createBandInfo({
        eventSource:    eventSource,
        date:           "Jul 28 2006 00:00:00 GMT",
        width:          "80%", 
        intervalUnit:   Timeline.DateTime.DAY, 
        intervalPixels: 100
    })
  ];
  bandInfos[0].syncWith = 1;
  bandInfos[0].highlight = true;
  tl = Timeline.create(document.getElementById("trac-timeline"), bandInfos, 1);
  Timeline.loadXML("/static/example1.xml", function(xml, url) { eventSource.loadXML(xml, url); });
}

mk_timeline();
*/
Timeline.loadXML("<?cs var:stimeline.xml_href ?>", function(xml, url) { es.loadXML(xml, url); });
</script>

<div id="help">
 <hr />
 <strong>Note:</strong> See <a href="<?cs var:trac.href.wiki ?>/TracTimeline">TracTimeline</a> 
 for information about the timeline view.<br />
 This page is powered by <a href="http://simile.mit.edu/timeline/">Simile Timeline</a>
</div>

</div>
<?cs include "footer.cs"?>
