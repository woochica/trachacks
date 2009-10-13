/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditor;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class WikiSourceEditor extends AbstractDecoratedTextEditor {

	public WikiSourceEditor() {
		super();
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

