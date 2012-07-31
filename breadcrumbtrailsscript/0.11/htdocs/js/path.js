document.write("<div id=\"pathnav\" class=\"nav\"><ul>");
var links = document.location.pathname.split("/");
var url = "";
for (i = 1;i < links.length;i++)
{
    if (links[i] == "") continue;
    var item = links[i];
    url += item;
    document.write("<li><a href=\"/"+url+"\">"+item+"</a></li>");
    url += "/";
}
document.write("</ul></div>");
