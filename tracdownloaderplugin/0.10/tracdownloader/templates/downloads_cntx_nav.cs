<?cs if:subcount(cntx_nav) > 1 ?>
<div id="ctxtnav" class="nav<?cs if in_adm ?> nav_admin<?cs /if ?>">
 <h2>Downloader Navigation</h2>
   <ul>
 <?cs set:count = 0 ?>
 <?cs each:item = cntx_nav ?><?cs
 set:count = count + 1 
 ?><li <?cs if:subcount(cntx_nav) == count ?>class="last"<?cs elif:count == 1 ?>class="first"<?cs /if?>><a href="<?cs
    var:item.0 ?>" <?cs if:item.1 == page_part ?>class="choosen"<?cs /if ?>><?cs var:item.2 ?></a></li><?cs
  /each ?>
  </ul>
</div><?cs 
/if ?>
