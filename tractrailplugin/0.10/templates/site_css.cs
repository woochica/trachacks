<?cs
##################################################################
# Site CSS - Place custom CSS, including overriding styles here.
?>


.trailnav ul {
  font-size: 10px;
  list-style: none;
  margin: 0px;
  padding: 0px;
  text-align: left;
  display: inline;
  }

.trailnav li {
 border-right: 1px solid #d7d7d7;
 display: inline;
 padding: 0 .75em;
 white-space: nowrap;
}

.trailnav li.last { border-right: none }

.trailnav h1 {
  display: inline;
  font-size: 10px;
  margin: 0;
  padding: 0px 7px;
}

div#trail {
  postion: fixed; top: 0px; left: 0px; z-index: 1000;
  padding: 3px;
  padding-bottom: 4px;
  border-bottom: 1px solid #d7d7d7;
  background-color: white;
  width: 100%;
}

 @media screen{
  body>div#trail {
   position: fixed;
  }
 }

 * html body{
  overflow:hidden;
 }

 html {
  margin-top: 30px;
}

