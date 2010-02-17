function HideContent(d) {
  if(d.length < 1) { return; }
  document.getElementById(d).style.display = "none";
}

function ShowContent(d) {
  if(d.length < 1) { return; }
  document.getElementById(d).style.display = "block";
}

function ReverseContentDisplay(d) {
  if(d.length < 1) { return; }
  if(document.getElementById(d).style.display == "none") { document.getElementById(d).style.display = "block"; }
  else { document.getElementById(d).style.display = "none"; }
}

function changeText(mydiv, newtext) {
  if (document.getElementById || document.all){
    if (document.getElementById) obj=document.getElementById(mydiv);
    else if (document.all) obj=document.all[mydiv];
    obj.innerHTML=newtext;
  }
}

function click_link(url) {
  var class = new XMLHttpRequest();
  class.overrideMimeType('text/html');
  class.open("GET", url, false);
  class.send(null);
  changeText('nar-detail', class.responseText);
  return false;
}
