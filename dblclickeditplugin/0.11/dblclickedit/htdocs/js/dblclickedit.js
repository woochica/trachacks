function myDblClickHandler(event) {
  document.location=document.location + "?action=edit";
}
document.ondblclick = myDblClickHandler;
