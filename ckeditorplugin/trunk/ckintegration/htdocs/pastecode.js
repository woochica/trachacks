CKEDITOR.plugins.add('pastecode', {
	getBasePath : function( )
	{
		return ck_tracwiki_path ? ck_tracwiki_path : this.path;
	},
	init : function(editor) {
		editor.addCommand('pcodeDialog', new CKEDITOR.dialogCommand('pcodeDialog'));
		editor.ui.addButton('PasteCode', {
			label : 'Quellcode einfügen', // TODO: translate (en: "Paste code")
			icon : this.getBasePath() + '/images/pastecode.png',
			command : 'pcodeDialog'
		});

		CKEDITOR.dialog.add('pcodeDialog', function(editor) {
			return {
				title : 'Quellcode einfügen', // TODO: translate (en: "Paste code")
				minWidth : 400,
				minHeight : 200,
				contents : [ {
					id : 'tab1',
					label : 'First Tab',
					title : 'First Tab',
					elements : 
					[ 
					  {
						id : 'code',
						// FIXME: why is style not working? (doesn't display textarea in monospace)
						style : 'font-family: monospace;',
						type : 'textarea',
						label : 'Code', // TODO: translate (en: "Code")
						setup : function( element )
						{
							var text = ''; // default value
							if (element)
							{
								if (element.getChildren())
								{
									var childs = element.getChildren();
									for (var i = 0; i < childs.count(); i++)
									{
										if (childs.getItem(i).getText().length > 0)
											text += childs.getItem(i).getText() + '\n';
									}
								} else
									text = element.getText();
							}
							this.setValue( text );
						},
						commit : function( element )
						{
							if ( element && element.getName() == 'pre' )
								element.appendText( this.getValue() );
						}
					  },
					  {
						id : 'pr_style',
						type : 'select',
						items: ck_code_styles,
						label : 'Syntax Highlighting', // TODO: translate (en: "Style (Syntax highlighting)")
						setup : function( element )
						{
						  	// default value; TODO: make it configurable
						  	var prog_lang = 'default'; 
						  	if ( element && element.data( 'code-style' ) )
						  		prog_lang = element.data( 'code-style' );
							this.setValue( prog_lang );
						},
						commit : function( element )
						{
							if ( element && element.getName() == 'pre' )
							{
								if ( this.getValue() )
									element.data( 'code-style', this.getValue() );
								else
									element.data( 'code-style', false );
							}
						}
					  } 
					]
				} ],
				onShow : function()
				{
					var sel = editor.getSelection();
					this.element = sel ? sel.getStartElement() : null;
					this.editMode = false;
					
					if ( this.element )
					{
						this.element = this.element.getAscendant( 'pre', true );
						if ( this.element )
						{
							var data_el = this.element.getAscendant( 'pre', false );
							if ( data_el && data_el.data('code-style') )
								this.element = data_el;
						}
					}
					
					if (!this.element || this.element.getName() != 'pre' )
						this.element = CKEDITOR.dom.element.createFromHtml( '<pre></pre>' );
					else
						this.editMode = true;
					
					this.setupContent( this.element );
					var field = this.getContentElement( 'tab1', 'code' );
					field.focus();
				},
				onOk: function () {
					if ( this.editMode )
					{
						this.element.setHtml( '' );
						this.commitContent( this.element );
					} else
					{
						this.element = CKEDITOR.dom.element.createFromHtml( '<pre></pre>' );
						this.commitContent( this.element );
						editor.insertElement( this.element );
					}
				}
			};
		});
	}
});
