<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include:"downloads_cntx_nav.cs" ?>
<div id="content">

<h1>Downloader <?cs var:filter.title ?> stats <?cs 
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
    var:href.base+'/'+item ?>" <?cs
   if:#item == #stats.year ?>class="choosen"<?cs /if ?>><?cs var:item ?></a></li><?cs 
 /each ?>
  <li class="last">&lt;- year</li>
  </ul>
</div>
<div class="wide_lst">
<ul>
 <?cs set:count = 0 ?>
 <?cs if:stats.year ?><?cs each:item = stats.months[stats.year] ?><?cs
      set:count = count + 1
     ?><li<?cs if:subcount(stats.months[stats.year]) == count ?> class="last"<?cs elif:count == 1 ?> class="first"<?cs /if?>><a href="<?cs
        var:href.base+'/'+stats.year+'/'+item ?>" <?cs
       if:#item == #stats.month ?>class="choosen"<?cs /if ?>><?cs var:item ?></a></li><?cs 
     /each ?>
      <li class="last">&lt;-<?cs if:!stats.month ?>select <?cs /if ?>month</li><?cs 
  else ?><li class="last">select year</li><?cs /if ?>
  </ul>
</div>

<div class="graph hor">
<div class="inside">
<table>
  <?cs each:row = stats.graph
    ?><tr>
      <td class="desc"><a href="<?cs var:href.base+'/'+row.3+'/daily' ?>"><?cs 
        var:row.0 ?></a></td>
      <td>
        <table class="coltab" >
          <tr><?cs
          if:#row.2 != 0 ?>
          <td class="col" style="width:<?cs var:row.2 ?>;"></td><?cs /if ?><td class="label<?cs
            if:#row.2 == 0 ?> zerowidthcol<?cs /if ?>">&nbsp;<?cs var:row.1 ?></td>
          </tr>
        </table>
      <span ></span></td>
    </tr><?cs
  /each ?>
</table>
</div>
</div>

</div>
<?cs include "footer.cs"?>
