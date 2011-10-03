/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.text.IDocument;
import org.eclipse.mylyn.wikitext.ui.editor.AbstractWikiTextDocumentProvider;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class TracWikiDocumentProvider extends AbstractWikiTextDocumentProvider{

	@Override
	public String getDefaultEncoding() {
		return TracWikiMarkupEditor.DEFAULT_ENCODING;
	}

	@Override
	protected void doSaveDocument(IProgressMonitor monitor, Object element, IDocument document, boolean overwrite) throws CoreException {
		String content = document.get();

		Page page = (Page) ((WikiEditorInput) element).getAdapter(Page.class);
		page.edit(content);
	}

}
