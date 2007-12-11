<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include:"downloads_cntx_nav.cs" ?>
<div id="content">

<h1>Downloader <?cs var:filter.title ?><?cs if:#stats.month != 0 ?>daily<?cs 
            else ?>monthly<?cs /if ?> stats<?cs 
    if:stats.year || stats.month?> for <?cs /if ?><?cs
    if:stats.month ?> month <?cs var:stats.month ?> <?cs /if ?><?cs 
    if:stats.year && stats.month?> in <?cs /if ?><?cs
    if:stats.year ?> year <?cs var:stats.year ?><?cs /if ?></h1>

<div class="wide_lst">
<ul>
 <?cs set:count = 0 ?>
 <?cs each:item = stats.years ?><?cs
  set:count = count + 1
 ?><li <?cs if:subcount(stats.years) == count ?>class="last"<?cs elif:count == 1 ?>class="first"<?cs /if?>><a href="<?cs
    var:href.daily.base+'/'+item ?>" <?cs
   if:#item == #stats.year ?>class="choosen"<?cs /if ?>><?cs var:item ?></a></li><?cs 
 /each ?>
  <li class="last">&lt;- year</li>
  </ul>
</div>
<div class="wide_lst">
<ul>
 <?cs set:count = 0 ?>
 <?cs each:item = stats.months[stats.year] ?><?cs
  set:count = count + 1
 ?><li <?cs if:subcount(stats.months[stats.year]) == count ?>class="last"<?cs elif:count == 1 ?>class="first"<?cs /if?>><a href="<?cs
    var:href.daily.base+'/'+stats.year+'/'+item ?>" <?cs
   if:#item == #stats.month ?>class="choosen"<?cs /if ?>><?cs var:item ?></a></li><?cs 
 /each ?>
  <li class="last">&lt;-<?cs if:!stats.month ?>select <?cs /if ?>month</li>
  </ul>
</div>

<div class="graph">
<div class="inside">
<table>
  <tr>
    <td><div class="colunvis"></div></td>
    <?cs each:cell = stats.graph
      ?><td><div class="col" style="height:<?cs
     var:cell.2 ?>px"></div></td>
    <?cs /each ?>
    <td><div class="colunvis"></div></td>
  </tr>
  <tr class="desc">
    <td><div class="colunvis"></div></td>
    <?cs each:cell = stats.graph
      ?><td><?cs
     var:cell.0 ?></td>
    <?cs /each ?>
    <td><div class="colunvis"></div></td>
  </tr>
  <tr class="unvis">
    <td></td><td></td>
    <?cs set:cntr=0 ?>
    <?cs each:cell = stats.graph
      ?><?cs set:cntr=cntr+1 ?><?cs if !(cntr % #3) ?><td colspan="3"><div class="flo" style="bottom: <?cs var:cell.3 ?>px"><?cs
       var:cell.1 
     ?></div></td><?cs /if ?>
    <?cs /each ?><?cs 
        if:(cntr % #3) == 1 ?><td></td><?cs 
        elseif:(cntr % #3) == 2 ?><td></td><td></td><?cs 
        /if ?>
  </tr>
  <tr class="unvis">
    <td></td>
    <?cs set:cntr=1 ?>
    <?cs each:cell = stats.graph
      ?><?cs set:cntr=cntr+1 ?><?cs if !(cntr % #3) ?><td colspan="3"><div class="flo" style="bottom: <?cs var:cell.3 ?>px"><?cs
       var:cell.1 
     ?></div></td><?cs /if ?>
    <?cs /each ?><?cs 
        if:(cntr % #3) == 1 ?><td></td><?cs 
        elseif:(cntr % #3) == 2 ?><td></td><td></td><?cs 
        /if ?>
  </tr>
  <tr class="unvis">
    <?cs set:cntr=2 ?>
    <?cs each:cell = stats.graph
      ?><?cs set:cntr=cntr+1 ?><?cs if !(cntr % #3) ?><td colspan="3"><div class="flo" style="bottom: <?cs var:cell.3 ?>px"><?cs
        var:cell.1 
     ?></div></td><?cs /if ?>
    <?cs /each ?><?cs 
        if:(cntr % #3) == 1 ?><td><?csvar:cntr?></td><?cs 
        elseif:(cntr % #3) == 2 ?><td></td><td></td><?cs 
        /if ?>
  </tr>
</table>
</div>
</div>

</div>
<?cs include "footer.cs"?>
