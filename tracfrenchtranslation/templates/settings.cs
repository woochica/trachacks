<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>Configuration et Gestion de session</h1>

 <h2>Paramètres utilisateur</h2>
 <p>
 Cette page vous permet de personnaliser les réglages de Trac.
 La configuration de la session est memorisée sur le serveur, et identifiée 
 grâce à une 'clef de session' contenue dans un cookie.
 Ce cookie permet à Trac de récupérer et d'utiliser vos réglages.
 </p>
 <form method="post" action="">
 <div>
  <h3>Informations personnelles</h3>
  <div>
   <input type="hidden" name="action" value="save" />
   <label for="name">Nom:</label>
   <input type="text" id="name" name="name" class="textwidget" size="30"
          value="<?cs var:settings.name ?>" />
  </div>
  <div>
   <label for="email">Courriel:</label>
   <input type="text" id="email" name="email" class="textwidget" size="30"
          value="<?cs var:settings.email ?>" />
  </div><?cs
  if:settings.session_id ?>
   <h3>Session</h3>
   <div>
    <label for="newsid">Clef de session:</label>
    <input type="text" id="newsid" name="newsid" class="textwidget" size="30"
           value="<?cs var:settings.session_id ?>" />
    <p>La clef de session est utilisée pour identifier les réglages personnels
   et les données de session sur le serveur. Par défaut, elle est générée 
   automatiquement, mais vous pouvez la modifier quand vous le souhaitez, si vous 
   voulez la rendre plus facilement mémorisable, de manière à l'utiliser sur un 
   autre navigateur</p>
   </div><?cs
  /if ?>
  <div>
   <br />
   <input type="submit" value="Enregistrer les changements" />
  </div >
 </div>
</form><?cs
if:settings.session_id ?>
 <hr />
 <h2>Recharger une session</h2>
 <p>Vous pouvez recharger une session précédemment crée en entrant votre clef ci-dessous,
puis en cliquant sur 'Recharger'. Ainsi, vous pouvez partager les réglages entre
plusieurs ordinateurs et/ou plusieurs navigateurs.</p>
 <form method="post" action="">
  <div>
   <input type="hidden" name="action" value="load" />
   <label for="loadsid">Clef de session existante:</label>
   <input type="text" id="loadsid" name="loadsid" class="textwidget" size="30"
          value="" />
   <input type="submit" value="Recharger" />
  </div>
 </form><?cs
/if ?>

</div>
<?cs include:"footer.cs"?>
