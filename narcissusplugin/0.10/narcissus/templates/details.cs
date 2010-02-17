<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head><meta http-equiv="content-type" content="text/html; charset=utf-8" /></head>
<body>
<div id="container"><div id="row">
  <h4>Details <a href="javascript:ReverseContentDisplay('details')">[+/-]</a></h4>
  <span style="display:block" id="details">
  <?cs if:subcount(ticket) > 0 ?>
    <?cs each:item = ticket ?>  
      <p><span class="nar-time"><?cs var:item.time ?></span> Ticket <a href="<?cs var:item.url ?>">
      #<?cs var:item.tid ?></a> <?cs var:item.action ?> by <?cs var:item.author ?></p>
    <?cs /each ?>
  <?cs /if ?>
  <?cs if:subcount(wiki) > 0 ?>
    <?cs each:item = wiki ?>  
      <p><span class="nar-time"><?cs var:item.time ?></span> <a href="<?cs var:item.url ?>">
      <?cs var:item.name ?></a> edited by <?cs var:item.author ?>
      <?cs if:item.diff ?>
        (<a href="<?cs var:item.url ?><?cs var:item.diff ?>">diff</a>)
      <?cs /if ?>
      </p>
    <?cs /each ?>
  <?cs /if ?>
  <?cs if:subcount(svn) > 0 ?>
    <?cs each:item = svn ?>  
      <p><span class="nar-time"><?cs var:item.time ?></span> Changeset <a href="<?cs var:item.url ?>">
      [<?cs var:item.rev ?>]</a> by <?cs var:item.author ?></p>
    <?cs /each ?>
  <?cs /if ?>
  </span>
</div>
<div id="row">
  <?cs if:subcount(score) > 0 ?>
    <h4>Score <a href="javascript:ReverseContentDisplay('score')">[+/-]</a></h4>
    <span style="display:none" id="score">
      <p>The following activity was detected:</p>
      <?cs each:item = score ?><p>
        <?cs var:item.eid ?> <?cs var:item.type ?>: <?cs var:item.activity ?><br />
      </p><?cs /each ?>
      <p>Activity level thresholds for <?cs var:bounds ?>: <a href="javascript:ReverseContentDisplay('bounds')">[+/-]</a></p>
      <span style="display:none" id="bounds">
        <ul><?cs each:item = bounds ?>
          <li><?cs var:item ?></li>
        <?cs /each ?></ul>
        <p>This score is used to calculate the brightness of the square.</p>
      </span>
    </span>
  <?cs /if ?>
  <div class="cleaner">&nbsp;</div>
</div></div>
</body>
</html>