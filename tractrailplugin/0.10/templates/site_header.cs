<?cs
####################################################################
# Site header - Contents are automatically inserted above Trac HTML
?>
<?cs def:trailnav(items) ?><?cs
 if:len(items) ?><ul><?cs
  set:idx = 0 ?><?cs
  set:max = len(items) - 1 ?><?cs
  each:trail_item = trail ?><?cs
   set:first = idx == 0 ?><?cs
   set:last = idx == max ?>
<li <?cs if:last ?> class="last" <?cs /if ?>><a href="<?cs var:trail_item[1]?>" title="<?cs var:trail_item[2] ?>"><?cs var:trail_item[0] ?></a></li><?cs
   set:idx = idx + 1 ?><?cs
  /each ?></ul><?cs
 /if ?><?cs
/def ?>

<div id="trail" class="trailnav">
<h1>Trail:</h1><?cs call:trailnav(trail) ?>
</div>
