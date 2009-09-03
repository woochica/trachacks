<?php

/*******************************************************************************
*  Title: Trac Create Web UI
*  Version: 0.0.1 @ August 31, 2009
*  Author: Shai Perednik
*  Website: http://www.csts.com
*  Original Code taken from http://www.easyphpcontactform.com/ and modified
********************************************************************************
*  COPYRIGHT NOTICE
*  Copyright 2009 Shai Perednik. All Rights Reserved.
*
*  This script may be used and modified free of charge by anyone
*  AS LONG AS COPYRIGHT NOTICES AND ALL THE COMMENTS REMAIN INTACT.
*  By using this code you agree to indemnify Shai Perednik or 
*  www.csts.com from any liability that might arise from 
*  it's use.
*
*  Selling the code for this program, in part or full, without prior
*  written consent is expressly forbidden.
*
*  Obtain permission before redistributing this software over the Internet
*  or in any other medium. In all cases copyright and header must remain
*  intact. This Copyright is in full effect in any country that has
*  International Trade Agreements with the India
*
*  Removing any of the copyright notices without purchasing a license
*  is illegal! 
*******************************************************************************/

/*******************************************************************************
 *	Script configuration - Refer README.txt
*******************************************************************************/

/* Form width in px or % value */
$form_width = '70%';

/* Form background color */
$form_background = '#F7F8F7';

/* Form border color */
$form_border = '#CCCCCC';

/* Form border style. Examples - dotted, dashed, solid, double */
$form_border_style = 'solid';

/* Empty/Invalid fields will be highlighted in this color */
$field_error_color = '#FF0000';

//Trac Base URL, relative to location of this script
$trac_base_url = "/trac";

//SVN Base URL, relative to location of this script
$svn_base_url = "/svn";

//Get the Server Path
$cur_domain = curDomain();

/* Success message to be displayed after the form is submitted. Can include HTML tags. Write your message 
between <!-- Start message --> and <!-- End message --> */
$success_message = <<<EOD
<!-- Start message -->
<p>Project Created, See below.</p><br /><br />
<br /><br /><br /><br /><br /><br /><br /><br />
<!-- End message -->
EOD;

/*******************************************************************************
 *	Do not change anything below, unless of course you know very well 
 *	what you are doing :)
*******************************************************************************/

$username = array('Username','username',NULL,NULL);
$short_name = array('Short Name','short_name',NULL,NULL);
$long_name = array('Long Name','long_name',NULL,NULL);;
$code = array('Code','captcha_code',NULL,NULL,NULL);

$error_message = '';

if (!isset($_POST['submit'])) {

  showForm();

} else { //form submitted

  $error = 0;
  
  if(!empty($_POST['username'])) {
  	$username[2] = clean_var($_POST['username']);
  	if (function_exists('htmlspecialchars')) $username[2] = htmlspecialchars($username[2], ENT_QUOTES);
  }
  else {
    $error = 1;
    $username[3] = 'color:#FF0000;';
  }
  
  if(!empty($_POST['short_name'])) {
  	$short_name[2] = clean_var($_POST['short_name']);
  	if (function_exists('htmlspecialchars')) $short_name[2] = htmlspecialchars($short_name[2], ENT_QUOTES);
  }
  else {
    $error = 1;
    $short_name[3] = 'color:#FF0000;';
  }
  
  if(!empty($_POST['long_name'])) {
  	$long_name[2] = clean_var($_POST['long_name']);
  	if (function_exists('htmlspecialchars')) $long_name[2] = htmlspecialchars($long_name[2], ENT_QUOTES);  	
  }
  else {
  	$error = 1;
    $long_name[3] = 'color:#FF0000;';
  }    

  if(empty($_POST['captcha_code'])) {
    $error = 1;
    $code[3] = 'color:#FF0000;';
  } else {
  	include_once "securimage.php";
		$securimage = new Securimage();
    $valid = $securimage->check($_POST['captcha_code']);

    if(!$valid) {
      $error = 1;
      $code[3] = 'color:#FF0000;';   
      $code[4] = '<strong><span style="color:#FF0000;">Incorrect code</span></strong>';
    }
  }

  if ($error == 1) {
    $error_message = '<span style="font-weight:bold;font-size:90%;">Please correct/enter field(s) in red.</span>';

    showForm();

  } else {
  	
  	if (function_exists('htmlspecialchars_decode')) $short_name[2] = htmlspecialchars_decode($short_name[2], ENT_QUOTES);
  	if (function_exists('htmlspecialchars_decode')) $long_name[2] = htmlspecialchars_decode($long_name[2], ENT_QUOTES);
	if (function_exists('htmlspecialchars_decode')) $username[2] = htmlspecialchars_decode($username[2], ENT_QUOTES);
    
    //RUN create SCRIPT HERE WITH VARIABLES FROM ABOVE
    $path_to_exec = "./sudo.py '$short_name[2]' '$long_name[2]' '$username[2]";
    $return_status_code = exec($path_to_exec, $output_array);
    echo "the whole return: " . implode("\n", $output_array);
    //END create SCRIPT SECTION
   
   //Do some error handling on $result here.
      include 'form-header.php';
      echo $GLOBALS['success_message'];
      echo "\n";
      echo "<p>Your Trac enviorment is at <a href='$cur_domain$trac_base_url'>$cur_domain$trac_base_url/$short_name[2]</a></p><br />
            <p>Your SVN enviorment is at <a href='$cur_domain$svn_base_url'>$cur_domain$svn_base_url/$short_name[2]</a></p><br /><br />";
      include 'form-footer.php';
       	
  }

} //else submitted



function showForm()

{
global $username, $short_name, $long_name, $code, $form_width, $form_background, $form_border, $form_border_style; 	
include 'form-header.php';
echo $GLOBALS['error_message'];  
echo <<<EOD
<div style="width:{$form_width};vertical-align:top;text-align:left;background-color:{$form_background};border: 1px {$form_border} {$form_border_style};overflow:visible;" id="formContainer">
<form method="post" class="contactForm">
<fieldset style="border:none;">
<p><label for="{$username[1]}" style="font-weight:bold;{$username[3]};width:25%;float:left;display:block;">{$username[0]}</label> <input type="text" name="{$username[1]}" value="{$username[2]}" /></p>
<p><label for="{$short_name[1]}" style="font-weight:bold;{$short_name[3]};width:25%;float:left;display:block;">{$short_name[0]}</label> <input type="text" name="{$short_name[1]}" value="{$short_name[2]}" /></p>
<p><label for="{$long_name[1]}" style="font-weight:bold;{$long_name[3]}width:25%;float:left;display:block;">{$long_name[0]}</label> <input type="text" name="{$long_name[1]}" value="{$long_name[2]}" /></p>
<p><label for="" style="font-weight:bold;width:25%;float:left;display:block;">&nbsp;</label> <img id="captcha" src="securimage_show.php" alt="CAPTCHA Image" /></p>
<p><label for="{$code[1]}" style="font-weight:bold;{$code[3]}width:25%;float:left;display:block;">{$code[0]}</label> <input type="text" name="{$code[1]}" size="10" maxlength="5" /> {$code[4]}</p>
<div style="margin-left:25%;display:block;">(Please enter the text in the image above. Text is not case sensitive.)<br />
<a href="#" onclick="document.getElementById('captcha').src = 'securimage_show.php?' + Math.random(); return false">Click here if you cannot recognize the code.</a>
</div>
<p><span style="font-weight:bold;font-size:90%;">All fields are required.</span></p>
<input type="submit" name="submit" value="Create Project" style="border:1px solid #999;background:#E4E4E4;margin-top:5px;" />
</fieldset>
</form>
</div>
<div style="width:{$form_width};text-align:right;font-size:80%;">
<a href="http://www.csts.com/" title="Created by Shai Perednik @ CSTS">Created by Shai Perednik @ CSTS</a>
</div> 
EOD;

include 'form-footer.php';
}

function clean_var($variable) {
    $variable = strip_tags(stripslashes(trim(rtrim($variable))));
  return $variable;
}


//Functions
function curDomain() {
    $pageURL = 'http';
    if ($_SERVER["HTTPS"] == "on") {$pageURL .= "s";}
    $pageURL .= "://" . $_SERVER["SERVER_NAME"];
    return $pageURL;
}
?>