/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.IVerticalRuler;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.mylyn.wikitext.core.WikiText;
import org.eclipse.mylyn.wikitext.ui.editor.WikiTextSourceEditor;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CTabFolder;
import org.eclipse.swt.custom.CTabItem;
import org.eclipse.swt.events.KeyAdapter;
import org.eclipse.swt.events.KeyEvent;
import org.eclipse.swt.events.MouseAdapter;
import org.eclipse.swt.events.MouseEvent;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.events.SelectionListener;
import org.eclipse.swt.widgets.Composite;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class TracWikiMarkupEditor extends WikiTextSourceEditor {

	public static final String ID = TracWikiMarkupEditor.class.getName();
	
	private static final String TRACWIKI_MARKUP_LANGUAGE = "TracWiki";

	private CTabFolder tabFolder;
	private CTabItem sourceTab;	
	private CTabItem previewTab;
	private TracWikiPreview preview;
	
	public TracWikiMarkupEditor() {
		super();
		setDocumentProvider(new TracWikiDocumentProvider());
//		setMarkupLanguage(WikiText.getMarkupLanguage(TRACWIKI_MARKUP_LANGUAGE));
	}



	@Override
	protected ISourceViewer createSourceViewer(Composite parent,	IVerticalRuler ruler, int styles) {
		setMarkupLanguage(WikiText.getMarkupLanguage(TRACWIKI_MARKUP_LANGUAGE));

		if(true) return super.createSourceViewer(parent, ruler, styles);
		
		tabFolder = new CTabFolder(parent, SWT.BOTTOM);
		ISourceViewer viewer = super.createSourceViewer(tabFolder, ruler, styles);
		
		{
			sourceTab = new CTabItem(tabFolder, SWT.NONE);
			sourceTab.setText("Wiki Source");
			sourceTab.setToolTipText("Wiki Source");			
			sourceTab.setControl(viewer instanceof Viewer ? ((Viewer) viewer).getControl() : viewer.getTextWidget());
			tabFolder.setSelection(sourceTab);
		}
		
		{
			previewTab = new CTabItem(tabFolder, SWT.NONE);
			previewTab.setText("Preview");
			previewTab.setToolTipText("Preview");
			preview = new TracWikiPreview(tabFolder);
			previewTab.setControl(preview.getBrowser());

			tabFolder.addSelectionListener(new SelectionListener() {
				public void widgetDefaultSelected(SelectionEvent selectionevent) {
					widgetSelected(selectionevent);
				}

				public void widgetSelected(SelectionEvent selectionevent) {
					if (tabFolder.getSelection() == previewTab) {
						Page page = ((WikiEditorInput) getEditorInput()).getWikiPage();
						String editorText = getDocumentProvider().getDocument(getEditorInput()).get();					
						preview.showPreview(page, editorText);
					}
				}
			});
		}
		
		return viewer;
	}
	
}
