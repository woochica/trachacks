/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.ui.editors.text.StorageDocumentProvider;

/**
 * @author ivan
 *
 */
public class WikiPageDocumentProvider extends StorageDocumentProvider {


	protected IDocument createDocument(Object element) throws CoreException {
		IDocument document = super.createDocument(element);
		// XXX
		
		return document;
	}
}
