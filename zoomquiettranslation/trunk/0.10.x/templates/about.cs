<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first<?cs if:!about.config_href ?> last<?cs /if ?>"><a href="<?cs
    var:trac.href.about ?>">概括</a></li><?cs
  if:about.config_href ?>
   <li><a href="<?cs var:about.config_href ?>">配置</a></li><?cs
  /if ?><?cs
  if:about.plugins_href ?>
   <li class="last"><a href="<?cs var:about.plugins_href ?>">插件</a></li><?cs
  /if ?>
 </ul>
</div>
<div id="content" class="about<?cs if:about.page ?>_<?cs var:about.page ?><?cs /if ?>">

 <?cs if:about.page == "config"?>
  <h1>配置</h1>
  <table><thead><tr><th class="section">Section</th>
   <th class="name">Name</th><th class="value">Value</th></tr></thead><?cs
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
   See <a href="<?cs var:trac.href.wiki ?>/TracIni">TracIni</a> for information about
   the configuration.
  </div>

 <?cs elif:about.page == "plugins" ?>
  <h1>Plugins</h1>
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
       Extension points:</th><?cs
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
  <h1>关于Trac <?cs var:trac.version ?>zh3</h1>
  <p>Trac是一个基于Web的软件项目管理及bug/事务追踪系统, 强调使用方便, 而不是其外在形式. 它提供了集成Wiki/版本控制系统界面, 以及更多方便的项目管理渠道, 来掌控项目的事件和变化.
</p>
  <p>Trac是以<a href = "http://sk.nvg.org/python/license.html">修订BSD许可证</a>分发的. 可以查看<a href="http://trac.edgewall.org/wiki/TracLicense">在线</a>的许可证的完整内容, 也可以查看分发中包含的<a href="http://trac.edgewall.org/browser/branches/0.10-stable/COPYING">COPYING文件</a>. </p>
  <a href="http://www.python.org/" style="border: none; float: right">
   <img style="display: block" src="<?cs var:htdocs_location ?>python.png"
     alt="python powered" width="140" height="56" />
  </a>
  <p>访问Trac开源项目网站
  <a href="http://trac.edgewall.org/">http://trac.edgewall.org/</a>.</p>
  <p>Copyright &copy; 2003-2006 <a href="http://www.edgewall.org/">Edgewall
  Software</a></p>
 <?cs /if ?>
</div>
<?cs include "footer.cs"?>
