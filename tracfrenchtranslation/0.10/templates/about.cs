<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>À propos de la navigation</h2>
 <ul>
  <li class="first<?cs if:!about.config_href ?> last<?cs /if ?>"><a href="<?cs
    var:trac.href.about ?>">Résumé</a></li><?cs
  if:about.config_href ?>
   <li><a href="<?cs var:about.config_href ?>">Configuration</a></li><?cs
  /if ?><?cs
  if:about.plugins_href ?>
   <li class="last"><a href="<?cs var:about.plugins_href ?>">Extensions</a></li>
   <?cs /if ?>
 </ul>
</div>
<div id="content" class="about<?cs if:about.page ?>_<?cs var:about.page ?><?cs /if ?>">

 <?cs if:about.page == "config"?>
  <h1>Configuration</h1>
  <table><thead><tr><th class="section">Section</th>
   <th class="name">Nom</th><th class="value">Valeur</th></tr></thead><?cs
  each:section = about.config ?><?cs
   if:len(section.options) ?>
    <tr><th class="section" rowspan="<?cs var:len(section.options) ?>"><?cs var:section.name ?></th><?cs
    each:option = section.options ?><?cs if:name(option) != 0 ?><tr><?cs /if ?>
     <td class="name"><?cs var:option.name ?></td>
     <td class="<?cs var:option.valueclass ?>"><?cs var:option.value ?></td>
    </tr><?cs
    /each ?><?cs
   /if ?><?cs
  /each ?></table>
  <div id="help">
   Voir <a href="<?cs var:trac.href.wiki ?>/TracIni">TracIni</a> pour obtenir des 
   informations sur la configuration.
  </div>

 <?cs elif:about.page == "plugins" ?>
  <h1>Extensions</h1>
  <dl id="plugins"><?cs
   each:plugin = about.plugins ?>
    <h2 id="<?cs var:plugin.module ?>.<?cs var:plugin.name ?>"><?cs var:plugin.name ?></h2>
    <table>
     <tr>
      <th class="module" scope="row">Module</th>
      <td class="module"><?cs var:plugin.module ?><br />
      <span class="path"><?cs var:plugin.path ?></span></td>
     </tr><?cs
     if:plugin.description ?><tr>
      <th class="description" scope="row">Description</th>
      <td class="description"><?cs var:plugin.description ?></td>
     </tr><?cs /if ?><?cs
     if:len(plugin.extension_points) ?><tr>
      <th class="xtnpts" rowspan="<?cs var:len(plugin.extension_points) ?>">
       Points d'extension:</th><?cs
       each:extension_point = plugin.extension_points ?><?cs
        if:name(extension_point) != 0 ?><tr><?cs /if ?>
        <td class="xtnpts">        
         <code><?cs var:extension_point.module ?>.<?cs var:extension_point.interface ?></code><?cs
          if:len(extension_point.extensions) ?> (<?cs
           var:len(extension_point.extensions) ?> extensions)<ul><?cs
           each:extension = extension_point.extensions ?>
            <li><a href="#<?cs var:extension.module ?>.<?cs
              var:extension.name ?>"><?cs var:extension.name ?></a></li><?cs
           /each ?></ul><?cs
          /if ?>
          <div class="description"><?cs var:extension_point.description ?></div>
        </td></tr><?cs
       /each ?><?cs
     /if ?>
    </table><?cs
   /each ?>
  </dl>

 <?cs else ?>
  <a href="http://trac.edgewall.org/" style="border: none; float: right; margin-left: 2em">
   <img style="display: block" src="<?cs var:chrome.href ?>/common/trac_banner.png"
     alt="Trac: Integrated SCM &amp; Project Management"/>
  </a>
  <h1>À propos de Trac <?cs var:trac.version ?></h1>
  <p>Trac est un système de gestion de projet logiciel et de suivi de défauts/bogues via le
  Web, qui met l'accent sur la facilité d'utilisation et évite les chichis.
  Il propose une interface pour le système de contrôle de source Subversion, un 
  Wiki intégré, et un nombre intéressant d'option permettant de rester au courant des évènements et
  changements d'un projet.</p>
  <p>Trac est distribué sous une licence BSD modifiée. Le texte entier de la licence peut être consulté
  <a href="http://trac.edgewall.org/wiki/TracLicense">en ligne</a> aussi bien que dans le fichier
  <tt>COPYING</tt> file inclus dans cette distribution.</p>
  <a href="http://www.python.org/" style="border: none; float: right">
   <img style="display: block" src="<?cs var:htdocs_location ?>python.png"
     alt="python powered" width="140" height="56" />
  </a>
  <p>Merci de consulter le projet open source Trac 
  <a href="http://trac.edgewall.org/">http://trac.edgewall.org/</a>.</p>
  <p>Copyright &copy; 2003-2006 <a href="http://www.edgewall.org/">Edgewall
  Software</a></p>
 <?cs /if ?>
</div>
<?cs include "footer.cs"?>
