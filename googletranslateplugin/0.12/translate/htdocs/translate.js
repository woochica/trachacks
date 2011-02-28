google.load("language", "1");

if(typeof String.prototype.trim !== 'function') {
  String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/g, ''); 
  }
}

function isAllTranslated(arr) {
 var i;
 for (i=0; i<arr.length; i++) {
  if (arr[i] == undefined) return false;
 }
 return true;
}

function translateTextNode(node, callback) {
	var text;
	if (node.nodeType!=3) return false;
	text = node.textContent;
	if (!text)
		text = node.nodeValue;
	text = text.trim();
	if (text == '') return false;
	var chunkSize = 200;
	var ind = 0;
	var textArr = new Array(Math.ceil(text.length/chunkSize));
	translateChunk = function(chunk) {
		google.language.translate({text:text.substring(chunk*chunkSize, (chunk+1)*chunkSize), type:'text'}, '', sessionLanguage, function(result) {
			if (result.status.code != 200) {
				textArr[chunk] = "[failed]";
			} else {
				textArr[chunk] = result.translation;
			}
			if (isAllTranslated(textArr)) {
				if (node.textContent)
					node.textContent=textArr.join('');
				else
					node.nodeValue=textArr.join('');
				callback();
			}
		});
	}
	for (ind=0; ind<=Math.floor(text.length/chunkSize); ind++) {
		translateChunk(ind);
	}
	return true;
}

function translateTree(element, callback) {
	var textNodes = new Array();
	var callCount = 0;
	var getTextNodes = function(e) {
		$(e).contents().each(function() {
			if (this.nodeType == 3) textNodes.push(this);
			else getTextNodes(this)
		});
	};
	getTextNodes(element);
	var i;
	for (i=0; i<textNodes.length; i++) {
		if (translateTextNode(textNodes[i], function() {
			callCount--;
			if (callCount == 0) callback();
		})) {
			callCount++;
		}
	}
}

function translateThis(comment, button, moreToCome) {
 if (moreToCome == undefined) moreToCome = false;
 if (button.val() == button.attr('backward')) return translateRevert(comment, button, moreToCome);
 if (comment.data('translatedText')) {
  if (!moreToCome) button.val(button.attr('backward'));
  comment.html(comment.data('translatedText'));
  return;
 }
 if (comment.html()) {
  button.val(button.attr('working'));
  comment.data('originalText', comment.html());
  translateTree(comment, function() {
   if (!moreToCome) button.val(button.attr('backward'));
   comment.data('translatedText', comment.html());
   });
 }
}

function translateRevert(comment, button, moreToCome) {
 if (comment.data('originalText')) {
  comment.html(comment.data('originalText'));
  if (!moreToCome) button.val(button.attr('forward'));
 }
}

$(document).ready(function() {
 $('div#content div div#changelog div.change input.translate').click(function() {
  var comment = $(this).closest('.change').find('.comment');
  translateThis(comment, $(this));
 });
 $('div#content div#ticket div.description input.translate').click(function() {
  var comment = $(this).closest('.description').find('.searchable');
  translateThis(comment, $(this), true);
  comment = $(this).closest('#ticket').find('h2');
  translateThis(comment, $(this));
 });
});
