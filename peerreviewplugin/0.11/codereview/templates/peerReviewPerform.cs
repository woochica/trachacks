<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav"> 
	<h2>Peer Review Navigation</h2> 
	<ul>
		<li class="first">
			<?cs if:main == "yes" ?>My Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewMain ?>">My Code Reviews</a>
			<?cs /if ?>
		</li>
		<li>
			<?cs if:create == "yes" ?>Create a Code Review
			<?cs else ?><a href="<?cs var:trac.href.peerReviewNew ?>">Create a Code Review</a>
			<?cs /if ?>
		</li>
		<li <?cs if:manager == 0 ?>class="last"<?cs /if ?>>
			<?cs if:search == "yes" ?>Search Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewSearch ?>">Search Code Reviews</a>
			<?cs /if ?>
		</li>
		<?cs if:manager == 1 ?>
		<li class="last">
			<?cs if:option == "yes" ?>Manager Options
			<?cs else ?><a href="<?cs var:trac.href.peerReviewOptions ?>">Manager Options</a>
			<?cs /if ?>
		</li>
		<?cs /if ?>
	</ul> 
</div> 

<br>
<b>File Information</b>
<br>

<table border="0" width="100%" style="border-collapse: collapse" id="infoTable">
    <tr>
        <td>
            Path: <?cs var:review.path ?>
        </td>
    </tr>
    <tr>
        <td>
            Revision: <?cs var:review.version ?>
        </td>
    </tr>
    <tr>
        <td>
            Start Line: <?cs var:review.lineStart ?><br>
    </tr>
    <tr>
    	<td>
            End Line: <?cs var:review.lineEnd ?><br>
        </td>
    </tr>
</table>
<br>

<table border="0" width="100%" style="border-collapse: collapse" id="table1">
    <tr>
        <td align="left"><font size="2">Click line number to Add/View comments</font></td>
        <td align="right"><font size="2">View <input type="text" id="SelectRangeTextBox" size="1" value="3"
	onKeyDown="if(event.keyCode == 13 || event.keyCode == 3){resetLines();}" style="text-align: center"> lines on either side of selection.</font>
        </td>
    </tr>
</table>

<!-- displays the contents of the file being reviewed -->
<div id="FilePreview">
<?cs var:file.rendered ?>
</div>

<br>
Back to the<a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:review.reviewID ?>"> Code Review Details</a> page
<br><br>

<div id="ViewCommentArea" style="position:absolute;left:0px;top:0px;z-index:1;display:none;width:455px;height:500px;" cellpadding="0" cellspacing="0">
<table width="450px" bgcolor="#F7F7F7" style="border-collapse: collapse;">
  <tr height="15px">
    <td id="ViewCommentTitle" width="432px" onmousedown="dragStart(event, 'ViewCommentArea');" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/top_bar_repeater_1x17.gif">
    </td>
    <td width="18px" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/close_btn_18x17.gif" onclick="closeCommentWindow('ViewCommentArea');"></td>
  </tr>
  <tr height="10px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td width="450px" align="center" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2">
      <div style="background-color: #F7F7F7; border: 1px solid #C0C0C0; overflow: auto; max-height: 400px; width: 425px" id="innerCommentDiv">
	Loading...
      </div>
    </td>
  </tr>
  <tr height="5px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td width="450px" align="right" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2" id="ViewAddCommentButtonArea">      
    </td>
  </tr>
  <tr height="3px">
    <td style="border-left: 1px solid #C8C8C8; border-bottom: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
</table>
</div>

<div id="AddCommentArea" style="position:absolute;left:0px;top:0px;z-index:1;display:none;width:305px;height:325px;">
<table width="300px" bgcolor="#F7F7F7" style="border-collapse: collapse;">
  <tr height="15px">
    <td id="AddCommentTitleArea" width="282px" onmousedown="dragStart(event, 'AddCommentArea');" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/top_bar_repeater_1x17.gif">
    </td>
    <td width="18px" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/close_btn_18x17.gif" onclick="closeCommentWindow('AddCommentArea');"></td>
  </tr>
  <tr height="10px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td valign="top" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2">
	<iframe frameborder="0" name="internalAddComment" id="internalAddComment" marginHeight="0" marginWidth="0" style="width:285px; height:196px" src="<?cs var:trac.href.peerReviewCommentCallback ?>"></iframe>
    </td>
  </tr>
  <tr height="2px">
    <td style="border-left: 1px solid #C8C8C8; border-bottom: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
</table>

</div>

<script type="text/javascript">
<!--
var baseUrl = "<?cs var:trac.href.peerReviewCommentCallback ?>";
var tacUrl = "<?cs var:trac.htdocs.thumbtac ?>";
var plusUrl = "<?cs var:trac.htdocs.plus ?>";
var minusUrl = "<?cs var:trac.htdocs.minus ?>";
var lineStart = <?cs var:review.lineStart ?>;
var lineEnd = <?cs var:review.lineEnd ?>;
//-->
</script>
<script type="text/javascript" src="<?cs
  var:chrome.href ?>/hw/js/peerReviewPerform.js"></script>

<style>
<!--
table.code th.performCodeReview {
        width: 4em;
}
//-->
</style>

<?cs include "footer.cs" ?>
