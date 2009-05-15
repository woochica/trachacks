/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentPartitioner;
import org.eclipse.jface.text.rules.FastPartitioner;
import org.eclipse.ui.editors.text.StorageDocumentProvider;

public class WikiDocumentProvider extends StorageDocumentProvider {
	private static final String Encoding = "utf-8";

	protected IDocument createDocument(Object element) throws CoreException {
		IDocument document = super.createDocument(element);
		if (document != null) {
			WikiPartitionScanner scanner = new WikiPartitionScanner();
			IDocumentPartitioner part = new FastPartitioner(scanner, scanner
					.getTokens());

			part.connect(document);
			document.setDocumentPartitioner(part);
		}

		return document;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * org.eclipse.ui.editors.text.StorageDocumentProvider#getDefaultEncoding()
	 */
	@Override
	public String getDefaultEncoding() {
		return Encoding;
	}

}
