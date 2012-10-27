
// Add comment button to standard wiki toolbar and wysiwyg plugin toolbar
jQuery(document).ready(function($) {

    function randomString() {
        var chars = "0123456789abcdef";
        var string_length = 32;
        var key = '';
        for (var i=0; i<string_length; i++) {
            var rnum = Math.floor(Math.random() * chars.length);
            key += chars.substring(rnum,rnum+1);
        }
        return key;
    }

    function addWikiCommentButton( textarea ) {
        function encloseSelection(prefix, suffix) {
            textarea.focus();
            var start, end, sel, scrollPos, subst;
            if (document.selection != undefined) {
                sel = document.selection.createRange().text;
            } else if (textarea.setSelectionRange != undefined) {
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
            if (document.selection != undefined) {
                var range = document.selection.createRange().text = subst;
                textarea.caretPos -= suffix.length;
            } else if (textarea.setSelectionRange != undefined) {
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

        var commentButton = $('<a href="#" id="wikicomment" title="Comment" tabindex="400" style="background:url('+_wikicomments_base+'/toolbar-comment-icon.png) no-repeat center"></a>');
        $(".wikitoolbar").width( $(".wikitoolbar").width() + 26 );
        $(".wikitoolbar").append( $(commentButton) );
        $(".wikitoolbar").children().last().click( function() { 
            var id = randomString();
            var dt = new Date();
            var timestamp = (dt.getFullYear()+"-"+(dt.getMonth() + 1)+"-"+dt.getDate()+" "+dt.getHours()+":"+dt.getMinutes()+":"+dt.getSeconds());
            encloseSelection(
                '\n{{{#!WikiComments author="'+_wikicomments_author+'" date="'+timestamp+'" id="'+id+'"\n',
                '\n='+id+'\n}}}\n'
            );
        });
    }

    function addWysiwygWikiCommentButton( list ) {
        var commentButton = $('<li title="Comment" class=""><a id="wt-comment" href="#" onmousedown="return false" tabindex="-1" style="background:url('+_wikicomments_base+'/toolbar-comment-icon.png) no-repeat center"></a></li>');
        $(list).width( $(list).width() + 26 );
        $(list).find("ul").first().append( $(commentButton) );
        $(commentButton).click(function(){
           $("textarea.wikitext").each(function() { 
              var instance = TracWysiwyg.findInstance( this );
              instance.formatCommentBlock();
           });
        });
    }

    $("textarea.wikitext").each(function() { addWikiCommentButton(this) });
    setTimeout(function() {
        TracWysiwyg.prototype.formatCommentBlock = function() {
            if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
                return;
            }
            var text = this.getSelectionText();
            if (!text) {
                var node = this.getFocusNode();
                while (node.nodeType == 3) {
                    node = node.parentNode;
                }
                text = TracWysiwyg.getTextContent(node);
                this.selectNode(node);
            }
        
            var fragment = this.getSelectionFragment();
            text = this.domToWikitext(fragment, { formatCodeBlock: true }).replace(/\s+$/, "");
        
            var d = this.contentDocument;
            var anonymous = d.createElement("div");
            var pre = d.createElement("pre");
            pre.className = "wiki macro";
            anonymous.appendChild(pre);
        
            var id = randomString();
            var dt = new Date();
            var timestamp = (dt.getFullYear()+"-"+(dt.getMonth() + 1)+"-"+dt.getDate()+" "+dt.getHours()+":"+dt.getMinutes()+":"+dt.getSeconds());
            var commentPrefix = '\n{{{#!WikiComments author="'+_wikicomments_author+'" date="'+timestamp+'" id="'+id+'"\n';
            var commentPostfix = '\n='+id+'\n}}}\n';

            if (text) {
                pre.appendChild(d.createTextNode(commentPrefix+text+commentPostfix));
            } else
                pre.appendChild(d.createTextNode(commentPrefix+commentPostfix));
        
            this.insertHTML(anonymous.innerHTML);
            this.selectionChanged();
        };
        $(".wysiwyg-toolbar").each(function() { addWysiwygWikiCommentButton(this) });
    }, 20);
});
