<?cs include "tracbb_header.cs"?>
<div id="content">
<h1>Buildbot Status Page</h1>
<h2>Builders</h2>
<?cs each:build = bb.builders ?>
<p>
<?cs if:build.status == "success" ?>
	<img src="<?cs var:chrome.href ?>/tracbb/bbsuccess.png" border="0"/> 
<?cs else ?>
	<img src="<?cs var:chrome.href ?>/tracbb/bberror.png" border="0"/> 
<?cs /if ?>
	
   <a href="<?cs var:build.url ?>"><?cs var:build.name ?></a>
   <?cs if:build.lastbuildurl ?>
   last build is <a href="<?cs var:build.lastbuildurl ?>">#<?cs var:build.lastbuild ?></a>
   <?cs else ?>
   no build available
   <?cs /if ?>
</p>
<?cs /each ?>
</div>
<?cs include "footer.cs"?>
