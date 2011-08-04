/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.text.source.SourceViewer;
import org.eclipse.mylyn.wikitext.core.parser.markup.MarkupLanguage;
import org.eclipse.mylyn.wikitext.tracwiki.core.TracWikiLanguage;
import org.eclipse.mylyn.wikitext.ui.editor.MarkupSourceViewer;
import org.eclipse.mylyn.wikitext.ui.editor.MarkupSourceViewerConfiguration;
import org.eclipse.mylyn.wikitext.ui.editor.ShowInTargetBridge;
import org.eclipse.swt.SWT;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditor;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class WikiSourceEditor extends AbstractDecoratedTextEditor {

	public WikiSourceEditor() {
		super();
//		MarkupLanguage markupLanguage = new TracWikiLanguage();
//		SourceViewer viewer = new MarkupSourceViewer(null, null, SWT.WRAP, markupLanguage);
//		// configure the viewer
//		MarkupSourceViewerConfiguration configuration = createSourceViewerConfiguration(taskRepository, viewer);
//
//		configuration.setMarkupLanguage(markupLanguage);
//		configuration.setShowInTarget(new ShowInTargetBridge(viewer));
//		viewer.configure(configuration);
//
//		// we want the viewer to show annotations
//		viewer.showAnnotations(true);		
		setSourceViewerConfiguration(new WikiSourceViewerConfiguration(getPreferenceStore()));
	}

	@Override
	public void doSave(IProgressMonitor progressMonitor) {
		String content = getDocumentProvider().getDocument(getEditorInput()).get();

		Page page = (Page) getEditorInput().getAdapter(Page.class);
		page.edit(content);
		
		super.doSave(progressMonitor);
	}

	
	
}

