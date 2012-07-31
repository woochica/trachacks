  document.write("<script type=\"text/javascript\" src=\"/trac/chrome/common/js/wikitoolbartemplatetext.js\"></script>");

  function encloseSelection(prefix, suffix, textarea) {
    textarea.focus();
    var start, end, sel, scrollPos, subst;
    if (typeof(document["selection"]) != "undefined") {
      sel = document.selection.createRange().text;
    } else if (typeof(textarea["setSelectionRange"]) != "undefined") {
      start = textarea.selectionStart;
      end = textarea.selectionEnd;
      scrollPos = textarea.scrollTop;
      sel = textarea.value.substring(start, end);
    }
    if (sel.match(/ $/)) { // exclude ending space char, if any
      sel = sel.substring(0, sel.length - 1);
      suffix = suffix + " ";
    }
    subst = prefix + sel + suffix;
    if (typeof(document["selection"]) != "undefined") {
      var range = document.selection.createRange().text = subst;
      textarea.caretPos -= suffix.length;
    } else if (typeof(textarea["setSelectionRange"]) != "undefined") {
      textarea.value = textarea.value.substring(0, start) + subst +
                       textarea.value.substring(end);
      if (sel) {
        textarea.setSelectionRange(start + subst.length, start + subst.length);
      } else {
        textarea.setSelectionRange(start + prefix.length, start + prefix.length);
      }
      textarea.scrollTop = scrollPos;
    }
  }

function WikiFormattingToolbar(textarea) {
  if ((typeof(document["selection"]) == "undefined")
   && (typeof(textarea["setSelectionRange"]) == "undefined")) {
    return;
  }
  
  var toolbar = document.createElement("div");
  toolbar.className = "wikitoolbar";

  function addButton(id, title, fn) {
    var a = document.createElement("a");
    a.href = "#";
    a.id = id;
    a.title = title;
    a.onclick = function() { try { fn() } catch (e) { } return false };
    a.tabIndex = 400;
    toolbar.appendChild(a);
  }


  addButton("strong", "Bold text: '''Example'''", function() {
    encloseSelection("'''", "'''", textarea);
  });
  addButton("em", "Italic text: ''Example''", function() {
    encloseSelection("''", "''", textarea);
  });
  addButton("heading", "Heading: == Example ==", function() {
    encloseSelection("\n== ", " ==\n", "Heading", textarea);
  });
  addButton("link", "Link: [http://www.example.com/ Example]", function() {
    encloseSelection("[", "]", textarea);
  });
  addButton("code", "Code block: {{{ example }}}", function() {
    encloseSelection("\n{{{\n", "\n}}}\n", textarea);
  });
  addButton("hr", "Horizontal rule: ----", function() {
    encloseSelection("\n----\n", "", textarea);
  });
  addButton("np", "New paragraph", function() {
    encloseSelection("\n\n", "", textarea);
  });
  addButton("br", "Line break: [[BR]]", function() {
    encloseSelection("[[BR]]\n", "", textarea);
  });

  textarea.parentNode.insertBefore(toolbar, textarea);

}

function WikiTemplatesToolbar(textarea)
{

  if ((typeof(document["selection"]) == "undefined")
   && (typeof(textarea["setSelectionRange"]) == "undefined")) {
    return;
  }

  var toolbarTemplates = document.createElement("div");
  toolbarTemplates.className = "wikitoolbartemplates";

  var tbtplList = document.createElement("select");
  var tbtplButton = document.createElement("input");
  tbtplButton.type = "button";
  tbtplButton.value = "Add";
  tbtplButton.onclick = function() { try { wikitoolbartpl_id = tbtplList.options[tbtplList.selectedIndex].value; tbtplList.options[tbtplList.selectedIndex].fn() } catch (e) { } return false };

  toolbarTemplates.appendChild(tbtplList);
  toolbarTemplates.appendChild(tbtplButton);

  function addTemplateItem(id, title, fn) {
    var a = document.createElement("option");
    a.value = id;
    a.text = title;
    a.fn = fn;
    tbtplList.options[tbtplList.length] = a;
  }

  function EncloseSelectionParseTemplate(tpl, textarea)
  {
	var re = /(<[A-Z0-9\s]+>)/;
	arrtpl = wikitoolbartpl_text[tpl].split(re);
	var tplparsed = "";
	var tplvars = new Array();
	for(arrtplcounter in arrtpl)
	{		
		if(re.test(arrtpl[arrtplcounter]))
		{
			bFound = false;
			for(tplvar in tplvars)
			{
				if(tplvars[tplvar][0] == arrtpl[arrtplcounter])
				{
					tplparsed += tplvars[tplvar][1];
					bFound = true;
					break;
				}
			}
			if(bFound == false)
			{
				tplvars[tplvars.length] = new Array();
				tplvars[tplvars.length-1][0] = arrtpl[arrtplcounter];
				tplvars[tplvars.length-1][1] = prompt(arrtpl[arrtplcounter], "");
				tplparsed += tplvars[tplvars.length-1][1];
			}
		}
		else
		{
			tplparsed += arrtpl[arrtplcounter];
		}
	}
	encloseSelection(tplparsed, "", textarea);
  }

  for(wikitoolbartpl_id in wikitoolbartpl_text)
  {
    addTemplateItem(wikitoolbartpl_id, wikitoolbartpl_description[wikitoolbartpl_id], function() {
      EncloseSelectionParseTemplate(wikitoolbartpl_id, textarea);
    });
  }

  textarea.parentNode.insertBefore(toolbarTemplates, textarea);

}

function addWikiToolbar(wikiToolbar)
{
// Add the toolbar to all <textarea> elements on the page with the class
// 'wikitext'.
  var re = /\bwikitext\b/;
  var textareas = document.getElementsByTagName("textarea");
  for (var i = 0; i < textareas.length; i++) {
    var textarea = textareas[i];
    if (textarea.className && re.test(textarea.className)) {
      wikiToolbar(textarea);
    }
  }
}

addWikiToolbar(WikiFormattingToolbar);
