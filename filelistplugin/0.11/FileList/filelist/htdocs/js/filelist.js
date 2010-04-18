$(document).ready(function(){
  var attachments = $("a[href$='wiki']").attr("href");
  attachments = attachments.replace('wiki', 'attachment/wiki/Files/?action=new&attachfilebutton=Attach+file');

//  $('.buttons').remove();
$('input[value="Edit this page"]').remove();
$('input[value="Delete this version"]').remove();
$('input[value="Delete page"]').remove();


  $('h3').each(function(){
    var h3 = $(this);
    if (h3.html() == "Attachments"){
        h3.next().remove();
        h3.remove();
//      h3.next().load(attachments + ' #attachment');
//      h3.html("Add Attachment");
//      $('input[name="cancel"]').remove();
    }
  });
});
