/*
Copyright (c) 2003-2011, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

(function()
{
	CKEDITOR.plugins.add( 'tracwiki',
	{
		requires : [ 'htmlwriter' ],

		init : function( editor )
		{
			var dataProcessor = editor.dataProcessor = new CKEDITOR.tracwikiDataProcessor( editor );

			dataProcessor.writer.forceSimpleAmpersand = editor.config.forceSimpleAmpersand;
		},

		onLoad : function()
		{
			! ( 'fillEmptyBlocks' in CKEDITOR.config ) && ( CKEDITOR.config.fillEmptyBlocks = 1 );
		}
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
				type: "POST", url: ck_render_url,
				data: ajax_data, dataType: "html", async: false
				//success: this.ajaxSuccess, error: this.ajaxError
				});
			// @todo: Error handling for AJAX request
			data = ajaxResponse.responseText;
			return data;
		},
		
		toDataFormat : function( html, fixForBody )
		{
			if ( 'html_wrapper' == ck_editor_type )
			{
				return '{{{\n#!html\n' + html + '\n}}}';
			}
			
			var writer = this.writer;
			
			this.getHtmlBlock = function( fragment )
			{
				writer.reset();
				fragment.writeHtml( writer, this.htmlFilter );
				return '{{{\n#!html\n' + writer.getHtml(true) + '\n}}}\n';
			};
			
			var list_str = '1. ';
			
			// @todo: Handle HTML->TracWiki conversion in an extensible way...
			this.parseFragment = function( fragment )
			{
				var data = '',
				    frag;
				for (var i = 0; i < fragment.children.length; i++)
				{
					frag = fragment.children[i];
					if (frag.name)
					{
						switch ( frag.name )
						{
							case 'h1':
								data += '= ' + this.parseFragment(frag) + ' =\n';
								break;
							
							case 'p':
								data += '\n' + this.parseFragment(frag) + '\n';
								break;
							
							case 'u':
								data += '__' + this.parseFragment(frag) + '__';
								break;
							
							case 'strong':
								data += "'''" + this.parseFragment(frag) + "'''";
								break;
							
							case 'em':
								data += "''" + this.parseFragment(frag) + "''";
								break;
								
							case 'span':
								if ( frag.attributes.class )
								{
									switch ( frag.attributes.class )
									{
										case 'underline':
											data += '__' + this.parseFragment(frag) + "__";
											break;
											
										default:
											data += this.getHtmlBlock(frag);
									}
								}
								break;
							
							case 'ol':
								list_str = '1. ';
								data += this.parseFragment(frag);
								break;
							
							case 'ul':
								list_str = '- ';
								data += this.parseFragment(frag);
								break;
							
							case 'li':
								data += list_str + this.parseFragment(frag) + '\n';
								break;
							
							default:
								data += this.getHtmlBlock(frag);
						}
					}
					else
					{
						data += frag.value;
					}
				}
				if ( '!' == data.substr(-1) )
					data += ' ';
				return data;
			};
			
			var fragment = CKEDITOR.htmlParser.fragment.fromHtml( html, fixForBody );
			return this.parseFragment(fragment);
		}
	};
})();
