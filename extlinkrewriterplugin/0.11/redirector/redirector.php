<html>
<?php
$afterSec = 1;
$requestUri = $_SERVER["REQUEST_URI"];
$startPos = strpos($requestUri, "?");

if ($startPos > 0) {
  $url = substr($requestUri, $startPos+1);
} else {
  $url = "";
}
?>
<head>
<meta http-equiv="Refresh" 
      content="<?php echo($afterSec); ?>;URL=<?php echo($url);?>" />
</head>
<body>
Jump to <a href="<?php echo($url);?>">
<?php echo($url);?>
</a>
after <?php echo($afterSec);?> sec.
</body>
</html>
