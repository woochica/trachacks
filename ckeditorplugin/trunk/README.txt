= General Notes =

The CKEdiotrPLugin is in a beta phase.

It was tested with 
 - CKEditor 3.6.2
 - Firefox 7 + 8
 - Internet Explorer 8 + 9
 

= Known Bugs / Limitations =

 - marker and text color is not working in headers (see 
   http://groups.google.com/group/trac-dev/browse_thread/thread/a6d12d574c3544ca)
 - when inserting an image, only image name as URL is not working 
   (even if there exists an image at that specific ticket / wiki entry)
 - when entering a link manually, it is printed with an exclemation mark;
   for example entering http://google.de is saved as http:!//google.de[[BR]]
 - copying lists from MS Word (tested with Word 2003) is not always working 
   completely (in some browsers it the deep intention is lost)
    

= Improvements Suggestions =

== technical improvements (suggestions) ==

The following approach might be a nicer solution as parsing the fragment and make a lot of 
recursive calls. This approach is also used by bbcode-plugin 
(see /CKEditor/_source/plugins/bbcode/plugin.js, line 135 and 311).

{{{
var parser = new CKEDITOR.htmlParser();
var parserText = '';

parser.onText = function( text )
{
	parserText += escapeFormatChars( text );
};

wiki = parser.parse( html );
}}}