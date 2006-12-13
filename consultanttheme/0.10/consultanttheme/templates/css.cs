<?cs
##################################################################
# Site CSS - Place custom CSS, including overriding styles here.
?>
/* CSS Document */
body{margin:0px; padding:0px; background:url(<?cs var:chrome.href ?>/theme/images/mainbg.gif) 0 0 repeat-x #F6F4E4; color:#6B6854; font:14px/18px "Trebuchet MS", Arial, Helvetica, sans-serif;}
div, p, ul, h1, h2, h4, img, form, label{padding:0px; margin:0px;}
ul{list-style-type:none;}

/*----MAIN PANEL----*/
#mainPan{width:80%; position:relative; margin:0 auto; padding:0px;}
/*----Left Panel----*/
#leftPan{width:240px; float:left;}
#leftTopPan{width:240px; height:125px; position:relative; margin:0 auto; padding:0; background:url(<?cs var:chrome.href ?>/theme/images/left-top.jpg) 0 0 no-repeat;}
#leftTopPan img{width:160px; height:39px; margin:30px 0 0 37px;}

#leftTopPan :link, #header :visited, #header :link:hover, #header :visited:hover {
 background: transparent;
 color: #555;
 margin-bottom: 2px;
 border: none;
}
#leftTopPan h1 :link:hover, #header h1 :visited:hover { color: #000 }

#leftPan ul{width:240px; height:231px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/menu-bg.jpg) 0 0 no-repeat; padding:28px 0 0;}
#leftPan ul li{width:118px; height:27px; position:relative; margin:0 auto; background:url(<?cs var:chrome.href ?>/theme/images/dot.gif) 0 100% repeat-x;}
#leftPan ul li a{width:96px; height:26px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/arrow-normal.gif) 0 50% no-repeat #F6F4E4; color:#8F8C73; font:13px/26px "Trebuchet MS", Arial, Helvetica, sans-serif; font-weight:bold; padding:0 0 0 22px; text-decoration:none;}
#leftPan ul li a:hover{background:url(<?cs var:chrome.href ?>/theme/images/arrow-normal.gif) 0 50% no-repeat #F6F4E4; color:#7F0A5F; text-decoration:none;}
#leftPan ul li.home{width:96px; height:27px; display:block; background: url(<?cs var:chrome.href ?>/theme/images/homebg.gif) 0 0 no-repeat #F6F4E4; color:#7F0A5F; font:13px/26px "Trebuchet MS", Arial, Helvetica, sans-serif; font-weight:bold; text-decoration:none; padding:0 0 0 22px;}
#leftPan ul li.contact{background:none;}

#leftPan ul.linkone{width:240px; height:259px; padding:0; background:none;}
#leftPan ul.linkone li{width:118px; height:26px; position:relative; margin:0 auto; background:none; padding:0px;}
#leftPan ul.linkone li a{width:96px; height:26px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/arrow-normal.gif) 0 50% no-repeat #F6F4E4; color:#8F8C73; font:13px/26px "Trebuchet MS", Arial, Helvetica, sans-serif; font-weight:normal; padding:0 0 0 22px; text-decoration:underline;}
#leftPan ul.linkone li a:hover{background:url(<?cs var:chrome.href ?>/theme/images/arrow-normal.gif) 0 50% no-repeat #F6F4E4; color:#25241E; text-decoration:underline;}

#leftPan h2{width:90px; height:63px; background:#F6F4E4; color:#8F146E; font-size:24px; line-height:63px; padding:0 0 0 63px; font-weight:normal;}

#leftPan form.big{width:222px; height:173px; position:relative; margin:0 auto; background:url(<?cs var:chrome.href ?>/theme/images/formbg.gif) 0 0 no-repeat #ABA894; color:#fff;}
#leftPan form.big input{width:143px; height:17px; margin:3px 0 2px 35px; }
#leftPan form.big label{width:143px; height:18px; margin:2px 0 0 35px; font:12px/15px Arial, Helvetica, sans-serif; font-weight:bold;}

#leftPan form.big input.button{width:51px; height:17px; float:left; background:url(<?cs var:chrome.href ?>/theme/images/button.gif) 0 0 no-repeat #FEFEFE; color:#fff; font-size:12px; font-weight:bold; line-height:18px; border:none; padding:0 10px 0 0;  margin:3px 10px 2px 28px; }

#leftPan form.big h2{width:150px; height:47px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/memberbg.gif) 0 0 no-repeat #D5D2BC; color:#fff; font-size:18px; line-height:47px; padding:0 0 0 65px;}
#leftPan form.big #register{width:100px; height:24px; float:left; margin:3px 0 0; }
#leftPan form.big #register a{display:block; background: url(<?cs var:chrome.href ?>/theme/images/arrow4.gif) 100% 50% no-repeat #ABA894; color:#fff; font-size:14px; padding:0 5px 0 0; text-decoration:none;}
#leftPan form.big #register a:hover{text-decoration:underline;}

#leftPan form.small{width:222px; height: 47px; position:relative; margin:0 auto; background:url(<?cs var:chrome.href ?>/theme/images/formbgsmall.png) 0 0 no-repeat #ABA894; color:#fff;}
#leftPan form.small div.centerer {text-align: center;}
#leftPan form.small h2{display:inline; background-color:#D5D2BC; color:#fff; font-size:18px; line-height:47px; padding: 0;}

/*----/Left Panel----*/

/*----Right Panel----*/
#rightPan{width:60%; float:left;}
#rightPan > h1{width:438px; height:124px; background:url(<?cs var:chrome.href ?>/theme/images/header.jpg) 0 0 no-repeat #D33F9F; color:#fff; font:20px/13px Georgia, "Times New Roman", Times, serif; padding:37px 0 0 13px;}
#rightPan > h1 span{font:13px/16px "Trebuchet MS", Arial, Helvetica, sans-serif;}
#rightPan h2,h3,h4,h5,h6 {margin: auto; padding: auto;}
/*
#rightPan h2{width:240px; height:36px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon1.jpg) 0 0 no-repeat #F6F4E4; color:#8F146E; font-size:24px; line-height:36px; padding:0 0 0 65px; margin:29px 0 0 9px;}

#rightPan h4{width:240px; height:50px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon2.jpg) 0 0 no-repeat #F6F4E4; color:#8F146E; font-size:24px; line-height:22px; padding:0 0 0 75px; margin:0 0 0 9px; clear:both;}
#rightPan h4 span{color:#9F9D81; background:#F6F4E4; font-size:16px; font-weight:bold; line-height:18px;}
*/
#rightPan p{padding:20px 0 0 9px;}
#rightPan p.bottompadding{padding:22px 0 0 9px; margin:0 0 38px 0;}
#rightPan p span.boldtext{font-weight:bold;}
#rightPan p span.magedacolortext{background:#F6F4E4; color:#8F146E;}
#rightmorePan{width:420px; height:28px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/pattern.gif) 0 0 repeat; border:1px solid #fff; line-height:28px; padding:0 0 0 20px; margin:0 0 0 9px;}
#rightmorePan p.textposition{float:left; padding:0 0 0 18px; margin:0px;}
#rightmorePan a{float:left; width:36px; height:28px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/morebg.gif) 0 0 no-repeat #D5D2BC; color:#1F1E15; text-decoration:none; padding:0 15px 0 45px; margin:0 0 0 135px;}
#rightmorePan a:hover{text-decoration:underline;}

#rightmorenextPan{width:420px; height:28px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/pattern.gif) 0 0 repeat; border:1px solid #fff; line-height:28px; padding:0 0 0 20px; margin:0 0 0 9px;}
#rightmorenextPan p.textposition{float:left; padding:0 0 0 18px; margin:0px;}
#rightmorenextPan a{float:left; width:36px; height:28px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/morebg.gif) 0 0 no-repeat #D5D2BC; color:#1F1E15; text-decoration:none; padding:0 15px 0 45px; margin:0 0 0 135px;}
#rightmorenextPan a:hover{text-decoration:underline;}


#rightaddPan{width:442px; height:170px; position:relative; margin:0 auto; padding:50px 0 0 9px;}
#rightaddonePan{width:218px; height:110px; float:left; background:url(<?cs var:chrome.href ?>/theme/images/image1.jpg) 100% 0 no-repeat #CBC8B2; color:#fff; }
#rightaddonePan p.whitetext{font-size:22px; padding:16px 0 0 16px;}
#rightaddonePan p.whitetextbig{font-size:28px; padding:10px 0 0 16px;}
#rightaddonePan a{width:97px; height:33px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/viewmore.jpg) 0 0 no-repeat #ABA894; color:#fff; font-size:16px; line-height:30px; text-decoration:none; margin:15px 0 0; padding:0 0 0 55px;}
#rightaddonePan a:hover{text-decoration:underline;}

#rightaddtwoPan{width:218px; height:110px; float:left; background:url(<?cs var:chrome.href ?>/theme/images/image2.jpg) 100% 0 no-repeat #CBC8B2; color:#fff; margin:0 0 0 6px;}
#rightaddtwoPan p.whitetext{font-size:22px; padding:16px 0 0 16px;}
#rightaddtwoPan p.whitetextbig{font-size:28px; padding:10px 0 0 16px;}

#rightaddtwoPan a{width:82px; height:33px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/viewmore.jpg) 0 0 no-repeat #ABA894; color:#fff; font-size:16px; line-height:30px; text-decoration:none; margin:15px 0 0; padding:0 0 0 55px;}
#rightaddtwoPan a:hover{text-decoration:underline;}

/*----/Right Panel----*/

/*----Footer Panel----*/
#footermainPan{background:url(<?cs var:chrome.href ?>/theme/images/footerbg.gif) 0 0 repeat-x #6B6854; color:#fff; position:relative; margin:0 auto; height:227px; clear:both;}
#footerPan{width:691px; position:relative; margin:0 auto; font:12px/15px "Trebuchet MS",Arial, Helvetica, sans-serif; font-weight:normal;}

#footerPan ul{width:546px; position:absolute; top:85px; left:42px;}
#footerPan li{float:left; }
#footerPan ul li a{padding:0 10px 0; color:#fff; background:#6B6854; text-decoration:none;}
#footerPan ul li a:hover{text-decoration:underline;}

#footerPan div.templateworld{background:#6B6854; color:#fff; display:block; position:absolute; top:160px; left:215px; }
/*#footerPan ul.templateworld li{height:20px;}*/
#footerPan div.templateworld a{background:#6B6854; display:inline; color:#fff; text-decoration:none; padding:0px;}
#footerPan div.templateworld a:hover{text-decoration:underline;}

#footerPan p.copyright{width:204px; background:#6B6854; color:#F3F1DF; position:absolute; top:105px; left:218px;}

#footerPanhtml{width:64px; height:19px; display:block; position:absolute; top:132px; left:240px;}
#footerPanhtml a{width:59px; height:18px; background:url(<?cs var:chrome.href ?>/theme/images/arrow2.gif) no-repeat 45px 0px #D0CEB8; display:block; position:absolute; top:0px; left:0px; line-height:19px; padding:1px 0 0 5px; border:1px solid #FFFFFA; color:#353427; text-transform:uppercase; text-decoration:none;}
#footerPanhtml a:hover{background:url(<?cs var:chrome.href ?>/theme/images/arrow3.gif) no-repeat 45px 0px #B0AD93; color:#353427; text-decoration:none;}

#footerPancss{width:64px; height:19px; display:block; position:absolute; top:132px; left:320px;}
#footerPancss a{width:49px; height:18px; background:url(<?cs var:chrome.href ?>/theme/images/arrow3.gif) no-repeat 45px 0px #D0CEB8; display:block; position:absolute; top:0px; left:0px;line-height:19px; padding:1px 0 0 15px; border:1px solid #FFFFFA; color:#353427; text-transform:uppercase; text-decoration:none;}
#footerPancss a:hover{background:url(<?cs var:chrome.href ?>/theme/images/arrow2.gif) no-repeat 45px 0px #B0AD93; color:#353427; text-decoration:none;}


#ctxtnav {
    margin-top: 8px;
}
