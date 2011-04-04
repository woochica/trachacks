$.fn.insertAtCaret = function (myValue) {
	return this.each(function(){
			//IE support
			if (document.selection) {
					this.focus();
					sel = document.selection.createRange();
					sel.text = myValue;
					this.focus();
			}
			//MOZILLA / NETSCAPE support
			else if (this.selectionStart || this.selectionStart == '0') {
					var startPos = this.selectionStart;
					var endPos = this.selectionEnd;
					var scrollTop = this.scrollTop;
					this.value = this.value.substring(0, startPos)+ myValue+ this.value.substring(endPos,this.value.length);
					this.focus();
					this.selectionStart = startPos + myValue.length;
					this.selectionEnd = startPos + myValue.length;
					this.scrollTop = scrollTop;
			} else {
					this.value += myValue;
					this.focus();
			}
	});
};

function addToDescription(upload) {
  if(upload.length)
  {
    //$('#field-description').val(text + '[[Image('+upload+')]]');
    $('#field-description').insertAtCaret('[[Image('+upload+')]]');
  }
}

$(document).ready(function() {
  
  $('#propertyform').attr('enctype', 'multipart/form-data');
  
  var addhref = $('.add-image').attr('href');
  var edithref = $('.edit-image').attr('href');
  var deletehref = $('.delete-image').attr('href');
  
  
  var upload = '\
<div class="upload">\
  <span>\
    <a class="uploadDescription" href="#"><img src="'+edithref+'"></a>\
    <input class="fileInput" type="file" name="attachment[]" />\
  </span>\
  <div class="field">\
    <label>Description of the file (optional):<br />\
    <input type="text" name="description[]" size="60" /></label>\
  </div>\
</div>';

var uploadContainer = '\
<fieldset>\
  <legend>Add Files</legend>\
  <div id="uploads" class="uploads">\
  </div>\
  <a class="addUpload" href="#" style="float:right"><img src="'+addhref+'"></a>\
</fieldset>';

$('#properties').next().html(uploadContainer);
  
  $('#uploads').append(upload);
     
  $('.uploadDescription').click(function(event) {
    event.preventDefault();
    addToDescription($(this));
  });
  
  $('.fileInput').change(function(event) {
    if($(this).val().match(/.((jpg)|(gif)|(jpeg)|(png))$/i))
        addToDescription($(this).val());
  });
            
  $('.addUpload').click(function(event) {
    event.preventDefault();
  
    $(this).parent().find('.uploads').append(upload);
    $(this).parent().find('.upload:last').find('.field').append('<a class="removeUpload" href="#"><img src="'+deletehref+'"></a>');
  
    $(this).parent().find('.removeUpload:last').click(function(event) { 
      event.preventDefault(); 
      $(this).parent().parent().remove(); 
    });
  
    $(this).parent().find('.uploadDescription:last').click(function (event) { 
      event.preventDefault(); 
      addToDescription($(this).next().val());
    });
    
    $(this).parent().find('.fileInput').change(function(event) {
      if($(this).val().match(/.((jpg)|(gif)|(jpeg)|(png))$/i))
        addToDescription($(this).val());
    });
    
  });
});
