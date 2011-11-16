/*
Copyright (c) 2003-2011, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

(function()
{
	// CONSTANTS
	/** special wiki format characters */
	var ESCAPE_WIKI_MARKUP = [ ["''", "!''"], // implies ["'''", "!'''"], 
	                   ['\\/\\/', '!//'], // alternative italic
	                   ['\\*\\*', '!**'], // alternative bold
	                   ['\\\\\\\\', '!\\\\'], // alternative BR (double backslashes)
	                   ['__', '!__'], 
	                   ['`', '!`'], 
	                   ['~~', '!~~'], 
	                   ['\\^', '!^'], 
	                   [',,', '!,,'], 
	                   ['!$', '! '], 
	                   ['\\|\\|', '!||'],
	                   ['\\[\\[', '![['] // macros
	                 ];
	
	/** format of text:
	 * null (default) HTML, keep formats
	 * 0 pasteFromWord, keep formats
	 * 1 pasteText, paste only text
	 */
	var defaultPasteFormat = null;
	
	function readConfig( config )
	{
		if (config)
		{
			if ( config.defaultPasteFormat == undefined || config.defaultPasteFormat == null )
				defaultPasteFormat = null;
			else if ( config.defaultPasteFormat == 0 || config.defaultPasteFormat == 1)
				defaultPasteFormat = config.defaultPasteFormat;
		}
	}
	
	function cleanHtmlEntities ( value )
	{
		value = value.replace(/&nbsp;/g, ' ');
		value = value.replace(/&quot;/g, '\"');
		value = value.replace(/&amp;/g, '\&');
		value = value.replace(/&lt;/g, '\<');
		value = value.replace(/&gt;/g, '\>');
		return value;
	}
	
	function escapeFormatChars( value )
	{
		for ( var i = 0; i < ESCAPE_WIKI_MARKUP.length; i++ )
		{
			var regex = new RegExp(ESCAPE_WIKI_MARKUP[i][0], "g");
			value = value.replace(regex, ESCAPE_WIKI_MARKUP[i][1]);
		}
		
		return value;
	}
	
	function getStyleAttribute( attr, regex, value )
	{
		var re = new RegExp("^" + attr + ":\s*(" + regex + ")", "i");
		var result = re.exec(value);
		if ( result != null )
		{
			return result[1];
		}
		return null;
	}
	
	CKEDITOR.plugins.add( 'tracwiki',
	{
		requires : [ 'htmlwriter' ],

		init : function( editor )
		{
			var dataProcessor = editor.dataProcessor = new CKEDITOR.tracwikiDataProcessor( editor );
			
			dataProcessor.writer.forceSimpleAmpersand = editor.config.forceSimpleAmpersand;
			readConfig( editor.config );
		},

		onLoad : function()
		{
			! ( 'fillEmptyBlocks' in CKEDITOR.config ) && ( CKEDITOR.config.fillEmptyBlocks = 1 );
		}
	});
	
	//When Pasting Text the Text is converted to wikiCode
	CKEDITOR.on('instanceReady', function ( editor ) {
		editor.editor.on('afterCommandExec', function ( event ) {
			var commandName = event.data.name;
			if ( !CKEDITOR.currentInstance )
				return;
			var dataProcessor = CKEDITOR.currentInstance.dataProcessor;
			
			if ( commandName == 'pastefromword' )
				dataProcessor.format = 0;
			else if ( commandName.substring(0,5) == 'paste')
				dataProcessor.format = 1;
			else
				dataProcessor.format = null;
		});
		
		editor.editor.on('paste', function ( editor ) {
			var dataProcessor = CKEDITOR.currentInstance ? CKEDITOR.currentInstance.dataProcessor : this.editor.dataProcessor;
			if ( editor.data.html )
			{
				if ( dataProcessor.format == null )				
					dataProcessor.format = defaultPasteFormat;
				editor.data.html = dataProcessor.toDataFormat(editor.data.html, "p");
			} else
			{
				dataProcessor.format = 1;
				editor.data.html = dataProcessor.toDataFormat(editor.data.text, "pre");
			}
		});
	});

	CKEDITOR.tracwikiDataProcessor = function( editor )
	{
		this.editor = editor;

		this.writer = new CKEDITOR.htmlWriter();
		this.dataFilter = new CKEDITOR.htmlParser.filter();
		this.htmlFilter = new CKEDITOR.htmlParser.filter();
	};

	CKEDITOR.tracwikiDataProcessor.prototype =
	{
		toHtml : function( data, fixForBody )
		{
			// @todo: Display a "load in progress" message somewhere
			
			// Transform TracWiki to HTML by requesting Trac server to do it using AJAX.
			var ajax_data = {};
			ajax_data["realm"] = ck_resource_realm;
			ajax_data["id"] = ck_resource_id;
			ajax_data["__FORM_TOKEN"] = form_token;
			ajax_data["text"] = data;
			var ajaxResponse = jQuery.ajax({
				type: "POST", url: trac_base_url + '/ck_wiki_render',
				data: ajax_data, dataType: "html", async: false
				//success: this.ajaxSuccess, error: this.ajaxError
				});
			// @todo: Error handling for AJAX request
			data = ajaxResponse.responseText;
			return data;
		},
		
		toDataFormat : function( html, fixForBody )
		{
			var list_str, offset = '', tablewidth, tableheight;
			var hpattern = /^h\d/i;
			var intablepattern = /t([d|h|r|body|head|able])/i;
			var inlistpattern = /([ol|ul])/i;
			var widthpattern = /width:\s(\d+)(px|%)/i;
			var heightpattern = /height:\s(\d+)(px|%)/i;
			var marginpattern = /margin-left:\s(\d+)px/i;
			var urlpattern = /(http:\/\/)?(.*\.[gif|jpg|png|bmp])/i;
			var programmingStyle = null;
			var onlyText = null;
			var code_lang = '';

			if ( 'html_wrapper' == ck_editor_type ) {
				return '{{{\n#!html\n' + html + '\n}}}';
			}
			
			var writer = this.writer;
			
			this.trim = function( line ){
				line = line.replace(/^\s*/,'');
				line = line.replace(/\s*$/,'');
				return line;
			}
			
			this.getHref = function ( href )
			{
				if (href == undefined || href == null)
					return href;
				var re = new RegExp('^(' + trac_base_url + ')+(.*)');
				var result = re.exec(href);
				if (result && result.length > 2 && result[1] != null && result[2] != null)
					href = result[2];
				return href;
			}
			
			this.getHtmlBlock = function( fragment )
			{
				writer.reset();
				fragment.writeHtml( writer, this.htmlFilter );
				return '[[html(' + writer.getHtml(true) + ')]]';
			};
			

			// @todo: Handle HTML->TracWiki conversion in an extensible way...
			this.parseFragment = function( fragment )
			{
				var data = '',
				 	frag,
					style;
				for (var i = 0; i < fragment.children.length; i++)
				{
					frag = fragment.children[i];
					
					if (this.programmingStyle == true && frag.name != 'pre')
					{
						if (frag.value)
							data += cleanHtmlEntities( frag.value );
						else if (frag.children)
							data += this.parseText(frag);
						continue;
					}
					
					if (frag.name)
					{
						var subcontent;
						var linebreaks;
						if (frag.attributes && frag.attributes.style
							&& (frag.name == 'span' || frag.name == 'div')
							)
						{
							subcontent = this.parseFragment(frag);
							var stylesArray = frag.attributes.style.split(';');
							// other styles than background-color or color should be ignored
							var allowedStyles = [ 'background-color', 'color' ];
							var style = '';
							
							for (var i2 = 0; i2 < stylesArray.length; i2++)
							{
								if (stylesArray[i2] == '')
									continue;
								for (i3 = 0; i3 < allowedStyles.length; i3++)
								{
									var s = getStyleAttribute(allowedStyles[i3], '.*', stylesArray[i2]);
									if (s)
										style += allowedStyles[i3] + ':' + s;
								}
							}
							
							var ending = "";
							if (subcontent.charAt(subcontent.length - 1) == ' ')
							{ 
								// make sure ending space is outside of macro
								// otherwise it will be omitted in Trac
								subcontent = subcontent.substring(0, subcontent.length - 1)
								ending = " ";
							}

							var macro_call = "";
							if (frag.name == 'span')
							{
								macro_call = '[[span(' + subcontent + ', style=' + style + ')]]'
							} else if (frag.name == 'div')
							{
								macro_call = '{{{#!div style="' + style + '"\n' + subcontent + '\n}}}'
							}	
							data += macro_call + ending;
							continue;
						} 
						
						switch (frag.name) {
						// Headlines
						case 'h1':
							data += '\n' + '= ' + this.parseFragment(frag) + ' = \n';
							break;
						case 'h2':
							data += '\n' + '== ' + this.parseFragment(frag) + ' == \n';
							break;
						case 'h3':
							data += '\n' + '=== ' + this.parseFragment(frag) + ' === \n';
							break;
						case 'h4':
							data += '\n' + '==== ' + this.parseFragment(frag) + ' ==== \n';
							break;
						case 'h5':
							data += '\n' + '===== ' + this.parseFragment(frag) + ' ===== \n';
							break;
						case 'h6':
							data += '\n' + '====== ' + this.parseFragment(frag) + ' ====== \n';
							break;

						// Textformat
						case 'u':
							data += '__' + this.parseFragment(frag) + '__';
							break;
						
						case 'b': //fall through
						case 'strong':
							data += "'''" + this.parseFragment(frag) + "'''";
							break;
						
						case 'i': // fall through
						case 'em':
							data += "''" + this.parseFragment(frag) + "''";
							break;
						case 'sup':
							data += '^' + this.parseFragment(frag) + '^';
							break;
						case 'sub':
							data += ',,' + this.parseFragment(frag) + ',,';
							break;
						case 'strike':
							data += '~~' + this.parseFragment(frag) + '~~';
							break;
						case 'del':
							data += '~~' + this.parseFragment(frag) + '~~';
							break;
						case 'tt':
							data += '`' + this.parseFragment(frag) + '`';
							break;
						case 'hr': // horizontal row
							data += '\n----\n';
							break;
						case 'a': // hyperlinks
							this.onlyText = true; // don't escape double slashes or other Wiki-Formatting
							subcontent = this.parseFragment(frag);
							this.onlyText = false;
							if (frag.attributes.rel && frag.attributes.rel.match('nofollow') != null)
							{
								subcontent = subcontent.replace("\?", "");
								data += subcontent;
							} else if (frag.attributes['class'] && frag.attributes['class'].match('wiki') != null)
							{
								data += subcontent;
							} else if ( subcontent.match(/\s*\[\[/) // image
									|| subcontent.match(/\s*#\d+/) // ticket number
									|| subcontent.match(/\s*\[\d+\]/) // revision number
									|| subcontent.match(/\s*\{\d+\}/) // report number
								)
							{
								data += subcontent; // it is an image
							} else if (frag.attributes.href)
							{
								var href = this.getHref( frag.attributes.href );
								if (subcontent.length > 0)
									data += "[" + href + " " + this.trim(subcontent) + "]";
								else
									data += href;
							} else
							{
								data += subcontent;
							}
							break;
						case 'img': // hyperlinks
							if (frag.attributes.src && frag.attributes.src.match(urlpattern))
							{
								var src = this.getHref( frag.attributes.src );
								data += '[[Image(' + src + ')]]';
							} else
								data += this.getHtmlBlock(frag);
							break;

						// Container
						case 'p':
							linebreaks = true;
							var offsetold = offset;
							offset += this.getMarginLeftOffset(frag);
							subcontent = this.parseFragment(frag);
							var par = frag.parent;
							while (par && par.name) {
								if (par.name.match("td|th|li") != null) {
									linebreaks = false;
									break;
								}
								par = parent.parent;
							}
							if (subcontent && (this.trim(subcontent)).length > 0) {
								if (linebreaks && !subcontent.match(/\n+$/i))
								{
									data += offset + subcontent + "\n\n";
								} 
								else
								{
									data += offset + subcontent;
								}
							}
							offset = offsetold;
							break;
						case 'blockquote':
							offset += ' ';
							data += this.parseFragment(frag);
							linebreaks =!data.match(/\n\n$/);
							if (linebreaks)
								data +='\n\n';
							offset = offset.replace(/^\s/, '');
							break;
						// when pasting from MS Word or OpenOffice, many font-nodes are present 
						case 'font':
							// fall through
						case 'div':
							data += this.parseFragment(frag);
							break;
						case 'pre':
							this.programmingStyle = true;
							var c = this.parseFragment(frag);
							c = c.replace(/\n*$/, "");
							
							if ( frag.attributes['data-code-style'] )
								this.code_lang = '#!' + frag.attributes['data-code-style'];

							if (c && c.length > 0)
							{
								data += '\n{{{';
								if ( this.code_lang )
									data += this.code_lang;
								data += '\n' + c + '\n}}}\n';
								frag.children = [];
							}
							this.code_lang = '';
							this.programmingStyle = false;
							break;
						case 'span':
							data += this.parseFragment(frag);
							break;

						case 'ul': // unordered List
							list_str = '- ';
							offset += ' ';
							data += this.parseFragment(frag)
							if (!frag.parent || !frag.parent.name || !frag.parent.name.match(inlistpattern))
								data += '\n\n';
							offset = offset.replace(/^\s/, '');
							break;
						case 'ol': // ordered list
							if (frag.attributes.start)
								list_str = frag.attributes.start + '. ';
							else
								list_str = '1. ';
							offset += ' ';
							data += this.parseFragment(frag)
							if (!frag.parent || !frag.parent.name || !frag.parent.name.match(inlistpattern))
								data += '\n';
							offset = offset.replace(/^\s/, '');
							break;
						case 'li':
							var subcontent = this.parseFragment(frag);
							data += '\n' + offset + list_str + subcontent;
							break;

						case 'br': // line break
							if (frag.parent && frag.parent.name) {
								var parentName = frag.parent.name;
								if (parentName.match(hpattern))
								{
									// ignore br-tags in headers
									break;
								} else if (!parentName.match(intablepattern) && 
										parentName != 'li') {
									data += '[[BR]]\n';
									break;
								} else
								{
									data += '[[BR]]';
								}
							}							
							break;

						case 'table': // table
							offset += ' ';
							if (frag.attributes.style && frag.attributes.style != null) {
								tablewidth = frag.attributes.style.match(widthpattern);
								tableheight = frag.attributes.style.match(heightpattern);
							}
							data += this.parseFragment(frag).replace(/\|---------------$/, '\n');
							offset = offset.replace(/^\s/, '');
							break;
						case 'tbody':
							data += this.parseFragment(frag);
							break;
						case 'thead':
							data += this.parseFragment(frag);
							break;
						// Complex Tables
						case 'tr':
							data += this.parseFragment(frag);
							if (frag.parent.name != 'tr')
								data += '\n' + offset + '|---------------';
							break;
						case 'th':
							data += '\n' + offset + '{{{#!th' + this.getTableCellAttributes(frag);
							data += '\n' + this.parseFragment(frag).replace("\n*$", "");
							data += '\n' + offset + '}}}';
							break;
						case 'td':
							data += '\n' + offset + '{{{#!td' + this.getTableCellAttributes(frag);
							data += '\n' + this.parseFragment(frag).replace("\n*$", "");
							data += '\n' + offset + '}}}';
							break;
						case 'col':							
							data+= this.parseFragment(frag);
							break;
						case 'colgroup':							
							data+= this.parseFragment(frag);
							break;
						default:
							data += this.getHtmlBlock(frag);
						}
					} else
					{
						var value = cleanHtmlEntities( frag.value );
						if ( !this.programmingStyle && !this.onlyText )
							value = escapeFormatChars( value );
						if (frag.parent && frag.parent.name && frag.parent.name.match('blockquote'))
							data += offset;
						data += value;
					}
				}
				
				return data;
			};

			this.getMarginLeftOffset = function(frag)
   			{
				var marginoffset = '';
				if (frag.attributes.style && frag.attributes.style != null) {
					var margin = frag.attributes.style.match(marginpattern);
					if (margin != null)
						for ( var j = 1; j < margin[1]; j += 40)
							marginoffset += ' ';
				}
				return marginoffset;
			}
			
			this.getTableCellAttributes = function(frag) {
				var attrib = '';
				attrib += ' style="' + this.getTableFieldWidth(frag) + this.getTableFieldHeight(frag) + 'background: #' + (frag.name == 'th' ? 'dde' : 'eef')
						+ '"';
				attrib += frag.attributes.colspan ? ' colspan=' + frag.attributes.colspan : '';
				attrib += frag.attributes.rowspan ? ' rowspan=' + frag.attributes.rowspan : '';
				attrib += frag.attributes.scope ? ' scope=' + frag.attributes.scope : '';
				attrib += frag.attributes.align ? ' align=' + frag.attributes.align : ' align=justify';
				attrib = attrib.replace(/undefined/g, '');
				return attrib;
			};

			this.getTableFieldHeight = function(frag) {
				var height = null;
				if (frag.attributes.style && frag.attributes.style != null)
					height = frag.attributes.style.match(heightpattern);
				if (height != null)
					return height[0] + '; ';
				else {
					var columncount = 0, row = frag, table = frag;
					while (row.name != 'tr' && row.parent.name.match(intablepattern) != null)
						row = row.parent;
					if (tableheight != null) {
						for ( var i = 0; i < row.children.length; i++) {
							var span = row.children[i].attributes.colspan ? row.children[i].attributes.colspan : 1;
							columncount += row.children[i].name == 'br' ? 0 : span;
						}
						var ownspan = frag.attributes.colspan ? frag.attributes.colspan : 1;
						height = 'height: ' + ((tableheight[1] / columncount) * ownspan) + '' + tableheight[2] + '; ';
					}
				}
				return (height == null) ? '' : height;
			};

			this.getTableFieldWidth = function(frag) {
				var width = null;
				if (frag.attributes.style && frag.attributes.style != null)
					width = frag.attributes.style.match(widthpattern);
				if (width != null)
					return width[0] + '; ';
				else {
					var columncount = 0, row = frag, table = frag;
					while (row.name != 'tr' && row.parent.name.match(intablepattern) != null)
						row = row.parent;
					if (tablewidth != null) {
						for ( var i = 0; i < row.children.length; i++) {
							var span = row.children[i].attributes.colspan ? row.children[i].attributes.colspan : 1;
							columncount += row.children[i].name == 'br' ? 0 : span;
						}
						var ownspan = frag.attributes.colspan ? frag.attributes.colspan : 1;
						width = 'width: ' + ((tablewidth[1] / columncount) * ownspan) + '' + tablewidth[2] + '; ';
					}
				}
				return (width == null) ? '' : width;
			};
			
			this.parseText = function( fragment )
			{
				var data = '',
				 	frag;
				for (var i = 0; i < fragment.children.length; i++)
				{
					frag = fragment.children[i];
					
					if ( frag.name == 'pre' && frag.children.length == 1 )
					{
						var value = frag.children[0].value;
						value = value.replace(/\n/g, '[[BR]]');
						data += value;
					} else if ( frag.name )
					{
						data += this.parseText(frag);
						switch ( frag.name )
						{
							case 'h1':
							case 'h2':
							case 'h3':
							case 'h4':
							case 'h5':
							case 'h6':
							case 'p':
							case 'br':
								// might be that it inserts duplicate break 
								// when it has an empty p-tag with br-tag
								// sometimes happens when copying from OO
								data += '[[BR]]';
						}
					} else
					{
						var value = cleanHtmlEntities( frag.value );
						value = escapeFormatChars( value );
						data += value;
					}
				}
				
				return data;
			};

			
			var fragment = CKEDITOR.htmlParser.fragment.fromHtml(html, fixForBody);
			var dataProcessor = this.editor.dataProcessor;
			var wiki = "";
			// reset vars before parsing
			this.programmingStyle = null;
			this.onlyText = null;
			this.code_lang = '';
			
			if ( !dataProcessor.format )
				wiki = this.parseFragment(fragment)
			else
				wiki = this.parseText(fragment);
			
			dataProcessor.format = null;
			this.editor.checkDirty();
			return wiki;
		}
	};
})();