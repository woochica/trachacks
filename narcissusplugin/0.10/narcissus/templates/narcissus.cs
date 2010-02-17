<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<?cs include "navigation.cs" ?>

<?cs if:error.exists == "yes" ?>
  <h1>Oops&hellip;</h1>
  <div id="content" class="error"><div class="message">
  <strong>Narcissus plugin has detected an error. Please fix the problem before continuing.</strong>
  <pre><p><?cs var:error.msg ?></p></pre>
  </div></div>
<?cs else ?>

<h1>Narcissus</h1>

<p>
  <a href="<?cs var:trac.href.narcissus ?>?view=group">Group View</a> | 
  <a href="<?cs var:trac.href.narcissus ?>?view=project">Project View</a> | 
  <a href="<?cs var:trac.href.narcissus ?>?view=ticket">Ticket View</a>
</p>


<div id="nar-container"><div id="nar-row">
  <div id="nar-left" style="float: left;"><div class="nar-vis-column-in" align="center">
    <p><?cs var:msg ?></p>
    <map name="vis">
      <?cs each:item = map ?>
        <area onclick="return click_link(href);" href="<?cs var:item.href ?>" shape="rect" coords="<?cs var:item.x1 ?>,<?cs var:item.y1 ?>,<?cs var:item.x2 ?>,<?cs var:item.y2 ?>" border="1" />
      <?cs /each ?>
    </map>
    <img src="<?cs var:vis ?>" border="0" width="<?cs var:vis.width ?>" height="<?cs var:vis.height ?>" usemap="#vis" />
  </div></div>

  <div id="nar-right" style="float: right;">
    <div class="nar-column-in" style="padding-top: 10px">
      <?cs if:subcount(date) > 0 ?>
        <form method="get" action="<?cs var:trac.href.narcissus ?>">
          <div class="date">
            <input type="hidden" name="view" value="<?cs var:view ?>" />
            <label>View from <input type="text" size="10" name="from" value="<?cs var:date.from ?>" /></label> to
            <label><input type="text" size="3" name="daysback" value="<?cs var:date.daysback ?>" /> days back</label>
            <input type="submit" name="update" value="Update" />
          </div>
        </form>
      <?cs /if ?>
      <?cs if:subcount(legend) > 0 ?>
        <h4>Legend</h4>
        <?cs each:item = legend ?>
          <p><img src="<?cs var:item ?>" width="<?cs var:item.width ?>" height="<?cs var:item.height ?>" align="absmiddle" />&nbsp;<?cs var:item.name ?></p>
        <?cs /each ?>
      <?cs /if ?>
    </div>
    <div class="nar-column-in" id="nar-detail">
    </div>
  </div>

  <div class="nar-cleaner">&nbsp;</div>

</div></div>
<?cs /if ?>

<?cs include "footer.cs" ?>

