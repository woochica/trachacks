/* Trac custom stylesheet for Python.org */

html, body {
  background: #ffffff;
  font-family: Arial, Verdana, Geneva, "Bitstream Vera Sans", Helvetica, sans-serif;
  font-size: 103%;
  margin: 0;
  padding: 0;
}

body :link, body :link:hover, body :visited {
  background: transparent no-repeat;
  border-bottom: 1px dashed #cccccc;
  color: #0000aa;
}

img {
  border: 0;
}

h1, h2, h3, h4, h5 {
  font-family: Georgia, "Bitstream Vera Serif", "New York", Palatino, serif;
  font-weight: normal;
}

h1 {
  color: #234764;
  font-size: 162%;
  margin: 0.7em 0 0.7em 0;
  text-decoration: none;
}

h2 {
  color: #366d9c;
  font-size: 140%;
  margin: 0.7em 0 0.7em 0;
}

h3 {
  color: #366d9c;
  font-size: 135%;
  font-style: italic;
  margin: 0.4em 0 0.4em 0;
}

h4 {
  color: #366d9c;
  font-size: 125%;
  margin: 0.4em 0 0.4em 0;
}

#banner {
  background: url(http://www.python.org/images/header-bg2.png);
  background-color: #f7f7f7;
  background-repeat: repeat-x;
  border: 0;
  border-bottom: 1px solid #999999;
  height: 84px;
  padding: 1px;
  z-index: 1;
}

#header {
  margin: 0px;
  padding: 10px 0 10px 0;
}

#logo {
  height: 71px;
  margin-left: 3%;
  margin-top: 10px;
  width: 211px;
}

#mainnav {
  background-color: transparent;
  background-image: none;
  border: 0;
  font-size: 75%;
  left: 3%;
  margin: 0;
  padding: 0;
  position: absolute;
  top: 100px;
  width: 16em;
  z-index: 1;
}

#mainnav ul {
  background: none;
  display: block;
  font-size: 100%;
  list-style: none;
  margin: 0 0 4px 1.4em;
  padding: 0;
  text-align: left;
}

#mainnav li {
  color: #3c4b7b;
  display: inline;
}

#mainnav :link, #mainnav :visited {
  background: transparent;
  border: 0;
  border-top: 1px solid #dddddd;
  display: block;
  font-family: Arial, Verdana, Geneva, "Bitstream Vera Sans", Helvetica, sans-serif;
  margin: 2px 0px 0px 2px;
  padding: 0.1em 0.1em 0.1em 0.1em;
  text-align: left;
  text-transform: none;
  width: 11em !important;
  width /**/: 11.2em;
}

#mainnav :link {
  color: #3c4b7b;
}

#mainnav :visited {
  color: #4c3b5b;
}

#mainnav :link:hover, #mainnav :visited:hover {
  background-color: transparent;
  border: 0;
  border-top: 1px solid #dddddd;
  color: black;
  text-decoration: underline;
}

#mainnav .active :link, #mainnav .active :visited {
  background: none;
  border: 0;
  border-top: 1px solid #dddddd;
  color: black;
}

#mainnav .active :link:hover, #mainnav .active :visited:hover {
  border: 0;
  border-top: 1px solid #dddddd;
}


* html #mainnav :link, * html #mainnav :visited {
  color: #4b5a6a;
}

#metanav {
  position: relative;
  top: 20px;
}

#main {
  font-family: Arial, Verdana, Geneva, "Bitstream Vera Sans", Helvetica, sans-serif;
  font-size: 85%;
  line-height: 1.4em;
}

#content {
  font-family: Arial, Verdana, Geneva, "Bitstream Vera Sans", Helvetica, sans-serif;
  left: 0;
  line-height: 1.4em;
  margin-left: 16.5em;
  padding: 0;
  z-index: 0;
}

#content.browser {
  padding: 0 0.55em 40px 0.0em;
}

#content.browser .first {
  background: transparent no-repeat;
  border-bottom: 1px dashed #cccccc;
  color: #0000aa;
}

#content.report {
  padding: 0 0.55em 40px 0.0em;
}

#content td.report {
  background: transparent no-repeat;
  border-bottom: 1px dashed #cccccc;
  color: #0000aa;
}

#content.roadmap {
  padding: 0 0.55em 40px 0.0em;
}

#content.roadmap {
  color: #234764;
}

.roadmap h1, .roadmap h2, .roadmap h3 {
  margin: 0;
}

#content.search {
  padding: 0 0.55em 40px 0.0em;
}

#content.ticket {
  padding: 0 0.55em 40px 0.0em;
}

#content.timeline {
  padding: 0 0.55em 40px 0.0em;
}

#content.timeline em {
  color: #234764;
}

#content.wiki .wikipage {
  padding: 0 0.55em 40px 0.0em;
}

.wikipage h1, .wikipage h2, .wikipage h3 {
  margin: 0;
}

#search {
  font-size: normal;
  font-weight: bold;
  height: 85px;
  padding: 0 5px 0 0;
  position: absolute;
  right: 4%;
  text-align: right;
  top: 5px;
  vertical-align: middle;
  white-space: nowrap;
  width: 28.1em;
  z-index: 1;
}

#search input {
  font-size: 150%;
}

#search input[id="proj-search"] {
  border: 1px solid #c4cccc;
  background-color: #ffffff;
  font-size: 171%;
  font-weight: normal;
  margin: 3px 0 0 0;
  padding: 1px 0 1px 0;
  vertical-align: top;
  width: 11em;
}

.buttons {
  margin-right: 0;
}

input[type="Submit"], input[type="Submit"]:hover {
  background-color: #f8f7f7;
  background-image: url(http://www.python.org/images/button-on-bg.png);
  background-repeat: no-repeat;
  border-bottom: 1px solid #6f7777;
  border-left: 1px solid #c4cccc;
  border-right: 1px solid #6f7777;
  border-top: 1px solid #c4cccc;
  color: #223344;
  font-family: Arial, Verdana, Geneva, "Bitstream Vera Sans", Helvetica, sans-serif;
  font-size: 110%;
  font-weight: bold;
  margin: 3px 0.4em 0px 0.4em;
  padding: 0px 0.2em 0px 0.2em;
  text-transform: lowercase;
}
