/* CSS Document */
body{padding:0px; margin:0px; background:#EFEFEF; color:#1A1A1A; font:14px/18px Arial, Helvetica, sans-serif;}
/*div, p, ul, h1, h2, h3, h4, h5, h6, h7{padding:0; margin:0;}*/
div, ul {padding:0; margin:0;}
ul{list-style-type:none;}
/*----MAIN PANEL----*/
#mainPan{width:100%; height: 100%;}
/*----Left Panel----*/
#leftPan{
    /*width:75%;*/
    background-image:url(<?cs var:chrome.href ?>/theme/images/bigheaderbg.png);
    background-repeat: no-repeat;
    background-color:#fff; 
    color:#1A1A1A;
    /*padding-right: 4px;*/
}
#logoPan img{margin:25px 0 0 10px;}
#logoPan a {border: 0;}
#logoPan hr {margin: 10px 0px;}

#leftbodyPan{margin:0 0 0 20px;}
/*
#leftbodyPan h2{width:175px; height:34px; background:url(<?cs var:chrome.href ?>/theme/images/icon1.jpg) 0 2px no-repeat #fff; color:#CC0000; font-size:22px; line-height:20px; padding:0 0 0 30px; font-weight:normal;}
#leftbodyPan h3{width:250px; height:75px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon3.jpg) 0 50% no-repeat #fff; color:#CC0000; font-size:24px; line-height:65px; padding:0 0 0 50px; font-weight:normal;}
#leftbodyPan h4{width:265px; height:90px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/image1.jpg) 0 0 no-repeat; margin:25px 0 34px; text-indent:-20000px;}
#leftbodyPan h5{width:134px; height:26px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon4.jpg) 0 0 no-repeat #fff; color:#CC0000; font:14px/26px "Trebuchet MS", Arial, Helvetica, sans-serif; padding:0 0 0 30px; margin:12px 0 10px 0;}
#leftbodyPan h5 span{font-weight:bold; background:#fff; color:#1A1A1A;}
#leftbodyPan h6{width:250px; height:75px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon6.jpg) 0 50% no-repeat #fff; color:#CC0000; font-size:24px; line-height:65px; padding:0 0 0 56px; font-weight:normal;}
*/

/*
#leftbodyPan ul{width:294px;}
#leftbodyPan ul li{width:294px; height:20px;}
#leftbodyPan ul li a{height:20px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon2-normal.gif) 0 7px no-repeat #fff; color:#1A1A1A; text-decoration:none; padding:0 0 0 20px; line-height:20px;}
#leftbodyPan ul li a:hover{background:url(<?cs var:chrome.href ?>/theme/images/icon2-hover.gif) 0 7px no-repeat #fff; color:#565555; text-decoration:none;}
*/

/*
#leftbodyPan p{padding:0 25px 0 0;}
#leftbodyPan p.border{border-bottom:1px solid #DCDCDC; padding:10px 0 0;}
#leftbodyPan p.bluetext{background:#fff; color:#0056B7; font-size:16px; font-weight:bold;}
#leftbodyPan p.blacktext{font-size:15px; font-weight:bold;}
#leftbodyPan p span.boldtext{font-style:italic; font-weight:bold;}
#leftbodyPan p.more{width:120px; height:48px;}
#leftbodyPan p.more a{height:38px; display:block; background:url(<?cs var:chrome.href ?>/theme/images/icon5.jpg) 0 0 no-repeat #fff; color:#CC0000; font:14px/20px "Trebuchet MS", Arial, Helvetica, sans-serif; padding:0 0 0 30px; text-decoration:none;}
#leftbodyPan p.more a:hover{text-decoration:underline;}
#leftbodyPan p.image{width:265px; height:90px; background:url(<?cs var:chrome.href ?>/theme/images/image2.jpg) 0 0 no-repeat; margin:25px 0 34px;}
*/
/*----/Left Panel----*/

/*----Right Panel----*/
#rightPan{width:334px; background:url(<?cs var:chrome.href ?>/theme/images/rightpanbg.gif) 0 0 repeat-y; vertical-align: top;}
#rightTopPan{width:334px; height:432px; background:url(<?cs var:chrome.href ?>/theme/images/menubg.jpg) 0 0 no-repeat;}

#rightTopPan ul{width:110px; position:relative; top:94px; left:30px;}
#rightTopPan ul li{height:27px; border-bottom:1px solid #E1E1E1;}
#rightTopPan ul li a{background:url(<?cs var:chrome.href ?>/theme/images/arrow.gif) 0 50% no-repeat; color:#1B0000; font:11px/26px "Trebuchet MS", Arial, Helvetica, sans-serif; padding:0 0 0 18px; text-decoration:none; text-transform:uppercase; border: none; overflow: hidden;}
#rightTopPan ul li a:hover{color:#CC0000;}

#rightTopPan ul li.active a{color:#CC0000;}
#rightTopPan ul li.last{border:none;}

/*
#rightBodyPan{width:238px; margin:0 0 0 31px;}
#rightBodyPan h2{width:150px; height:46px; background:url(<?cs var:chrome.href ?>/theme/images/icon7.jpg) 0 2px no-repeat #EFEFEF; color:#CC0000; font-size:22px; line-height:20px; padding:28px 0 0 40px; font-weight:normal;}

#rightBodyPan p.largeblack{font-size:16px; font-weight:bold; padding:0 0 12px 0;}
#rightBodyPan p.blue-italictext{background:#EFEFEF; color:#015DC6; font-size:15px; font-style:italic; padding:12px 0 48px 0;}
#rightBodyPan p.morenext{width:238px; height:50px; display:block;}
#rightBodyPan p.morenext a{width:74px; height:30px; display:block; margin:0; background:url(<?cs var:chrome.href ?>/theme/images/icon8.jpg) 62% 0 no-repeat #fff; color:#1A1A1A; line-height:30px; text-decoration:none; padding:0 0 0 164px;}
#rightBodyPan p.morenext a:hover{background:url(<?cs var:chrome.href ?>/theme/images/icon8-hover.jpg) 62% 0 no-repeat #DFDFDF; color:#1A1A1A; text-decoration:none;}
*/

/*----FOOTER PANEL----*/
#footermainPan{background:#4C4C4C url(<?cs var:chrome.href ?>/theme/images/footerbg.gif) -15em 0 repeat-y; color:#fff; font-size: 10px; padding: 10px 0;}
#footerPan{background:url(<?cs var:chrome.href ?>/theme/images/footerbg.gif) 0 0 repeat-y;}

/*#footerPan img{width:248px; height:38px; position:absolute; top:23px; right:6px;}*/

#footerPan ul{width:80%; position:relative; top:49px; left:53px;}
#footerPan li{font:11px/15px "Trebuchet MS",Arial, Helvetica, sans-serif; font-weight:normal;}
#footerPan ul li a{padding:0 5px 0; color:#fff; background:#4C4C4C; text-decoration:none;}
#footerPan ul li a:hover{text-decoration:underline;}

#footerPan :link, #footerPan :visited { color: #bbb; }
#footerPan #tracpowered { border: 0; float: left }
#footerPan #tracpowered:hover { background: transparent }
#footerPan p { margin: 0 }
#footerPan p.left {
  float: left;
  margin-left: 1em;
  padding: 0 1em;
}
#footerPan p.right {
  float: right;
  text-align: right;
  padding: 0 1em;
}

/* --- FIX TRAC STUFF --- */
table.listing { clear: none; }
#content {padding-right: 15px;}
