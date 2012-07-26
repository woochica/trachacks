<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">

<head>
<title><?cs var:title ?></title>
<!-- metadata -->
<meta name="generator" content="Trac" />
<meta name="version" content="Trac <?cs var:trac.version ?>" />
<meta name="presdate" content="20050728" />
<meta name="author" content="<?cs var:trac.authname ?>" />
<meta name="company" content="Edgewall" />
<!-- configuration parameters -->
<meta name="defaultView" content="slideshow" />
<meta name="controlVis" content="hidden" />
<!-- style sheet links -->
<link rel="stylesheet" href="<?cs var:chrome.href?>/slideshow/ui/<?cs var:theme ?>/slides.css" type="text/css" media="projection" id="slideProj" />
<link rel="stylesheet" href="<?cs var:chrome.href?>/slideshow/ui/<?cs var:theme ?>/outline.css" type="text/css" media="screen" id="outlineStyle" />
<link rel="stylesheet" href="<?cs var:chrome.href?>/slideshow/ui/<?cs var:theme ?>/print.css" type="text/css" media="print" id="slidePrint" />
<link rel="stylesheet" href="<?cs var:chrome.href?>/slideshow/ui/<?cs var:theme ?>/opera.css" type="text/css" media="projection" id="operaFix" />
<!-- S5 JS -->
<script src="<?cs var:chrome.href?>/slideshow/ui/<?cs var:theme ?>/slides.js" type="text/javascript"></script>
</head>
<body>

<div class="layout">
<div id="controls"><!-- DO NOT EDIT --></div>
<div id="currentSlide"><!-- DO NOT EDIT --></div>
<div id="header"></div>
<div id="footer">
<?cs if:location ?>
<h1><?cs var:location ?></h1>
<?cs /if ?>
<?cs if:title ?>
<h2><?cs var:title ?></h2>
<?cs /if ?>
</div>

</div>


<div class="presentation">

<div class="slide">
<?cs var:title_page ?>
</div>

<?cs each:slide = slides ?>
<div class="slide">
<?cs var:slide.body ?>

<?cs if:slide.handout ?>
<div class="handout">
<?cs var:slide.handout ?>
</div>
<?cs /if ?>

</div>
<?cs /each ?>


</div>

</body>
</html>
