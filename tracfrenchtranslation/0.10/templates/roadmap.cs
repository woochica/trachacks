<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="roadmap">
 <h1>Feuille de route</h1>

 <form id="prefs" method="get" action="">
  <div>
   <input type="checkbox" id="showall" name="show" value="all"<?cs
    if:roadmap.showall ?> checked="checked"<?cs /if ?> />
   <label for="showall">Montrer les jalons déjà atteints</label>
  </div>
  <div class="buttons">
   <input type="submit" value="Actualiser" />
  </div>
 </form>

 <ul class="milestones"><?cs each:milestone = roadmap.milestones ?>
  <li class="milestone">
   <div class="info">
    <h2><a href="<?cs var:milestone.href ?>">Jalon: <em><?cs
      var:milestone.name ?></em></a></h2>
    <p class="date"<?cs
     if:milestone.completed_date ?> title="<?cs var:milestone.completed_date ?>">
      Atteint <?cs var:milestone.completed_delta ?> avant<?cs
     elif:milestone.due_date ?> title="<?cs var:milestone.due_date ?>"><?cs
      if:milestone.late ?>
       <strong><?cs var:milestone.due_delta ?> en retard</strong><?cs
      else ?>
       Prévu pour <?cs var:milestone.due_delta ?><?cs
      /if ?><?cs
     else ?>>
      Pas de date définie<?cs
     /if ?>
    </p><?cs
    with:stats = milestone.stats ?><?cs
     if:#stats.total_tickets > #0 ?>
      <table class="progress">
       <tr>
        <td class="closed" style="width: <?cs
          var:#stats.percent_closed ?>%"><a href="<?cs
          var:milestone.queries.closed_tickets ?>" title="<?cs
          var:#stats.closed_tickets ?> de <?cs
          var:#stats.total_tickets ?> tickets<?cs
          if:#stats.total_tickets != #1 ?>s<?cs /if ?> fermés"></a></td>
        <td class="open" style="width: <?cs
          var:#stats.percent_active ?>%"><a href="<?cs
          var:milestone.queries.active_tickets ?>" title="<?cs
          var:#stats.active_tickets ?> sur <?cs
          var:#stats.total_tickets ?> tickets<?cs
          if:#stats.total_tickets != #1 ?>s<?cs /if ?> actifs"></a></td>
       </tr>
      </table>
      <p class="percent"><?cs var:#stats.percent_closed ?>%</p>
      <dl>
       <dt>Tickets fermés:</dt>
       <dd><a href="<?cs var:milestone.queries.closed_tickets ?>"><?cs
         var:stats.closed_tickets ?></a></dd>
       <dt>Tickets actifs:</dt>
       <dd><a href="<?cs var:milestone.queries.active_tickets ?>"><?cs
         var:stats.active_tickets ?></a></dd>
      </dl><?cs
     /if ?><?cs
    /with ?>
   </div>
   <div class="description"><?cs var:milestone.description ?></div>
  </li><?cs
 /each ?></ul><?cs
 if:trac.acl.MILESTONE_CREATE ?>
  <div class="buttons">
   <form method="get" action="<?cs var:trac.href.milestone ?>"><div>
    <input type="hidden" name="action" value="new" />
    <input type="submit" value="Créer un nouveau jalon" />
   </div></form>
  </div><?cs
 /if ?>

 <div id="help">
  <strong>Note:</strong> Voir <a href="<?cs
    var:trac.href.wiki ?>/TracRoadmap">TracRoadmap</a> pour de l'aide sur 
    l'utilisation du planning.
 </div>

</div>
<?cs include:"footer.cs"?>
