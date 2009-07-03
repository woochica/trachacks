/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.ui.editors.text.TextEditor;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class WikiEditor extends TextEditor {

	public WikiEditor() {
		super();
		
	}

	@Override
	public void doSave(IProgressMonitor progressMonitor) {
		String content = getDocumentProvider().getDocument(getEditorInput()).get();

		Page page = (Page) getEditorInput().getAdapter(Page.class);
		page.edit(content);
		
		super.doSave(progressMonitor);
	}

	
	
}
