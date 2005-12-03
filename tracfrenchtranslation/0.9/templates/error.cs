<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="error">

 <?cs if error.type == "TracError" ?>
  <h3><?cs var:error.title ?></h3>
  <p class="message">
  <?cs var:error.message ?>
  </p>

 <?cs elif error.type == "internal" ?>
  <h3>Aïe...</h3>
  <div class="message">
   <strong>Trac a detecté une erreur interne:</strong>
   <pre><?cs var:error.message ?></pre>
  </div>
  <p>
   Si vous pensez que cette action aurait du fonctionner et si vous pouvez reproduire le probleme, 
   vous devriez envisager de reporter ce problème l'équipe de Trac.
  </p>
  <p>
   Rendez vous sur <a href="<?cs var:trac.href.homepage ?>"><?cs
     var:trac.href.homepage ?></a>  et créez un nouveau ticket où vous décrirez
   le problème, et comment le reproduire. N'oubliez pas d'include la pile d'appel Python
   affichée ci-dessous.
  </p>

 <?cs elif error.type == "permission" ?>
  <h3>Permission refusée</h3>
  <p class="message">
  <?cs var:error.message ?>
  </p>
  <div id="help">
   <strong>Note</strong>: Voir
   <a href="<?cs var:trac.href.wiki ?>/TracPermissions">TracPermissions</a> pour de 
   l'aide sur la gestion des permissions.
  </div>

 <?cs /if ?>

 <p>
  <a href="<?cs var:trac.href.wiki ?>/TracGuide">TracGuide</a>
  &mdash; Le Guide de l'utilisateur et de l'administrateur de Trac
 </p>

 <?cs if $error.traceback ?>
  <h4>Pile d'appel Python</h4>
  <pre><?cs var:error.traceback ?></pre>
 <?cs /if ?>

</div>
<?cs include "footer.cs"?>
