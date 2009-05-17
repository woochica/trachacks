package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.jface.text.DefaultPositionUpdater;
import org.eclipse.jface.text.DocumentPartitioningChangedEvent;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentPartitioningListener;
import org.eclipse.jface.text.IDocumentPartitioningListenerExtension2;
import org.eclipse.jface.text.IPositionUpdater;
import org.eclipse.jface.viewers.AbstractTreeViewer;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.texteditor.IDocumentProvider;
import org.eclipse.ui.views.contentoutline.ContentOutlinePage;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.editor.model.WikiSection;
import org.trachacks.wikieditor.eclipse.plugin.editor.model.WikiTextParser;

public class WikiContentOutlinePage extends ContentOutlinePage implements
		IDocumentPartitioningListener, IDocumentPartitioningListenerExtension2 {
	private WikiSourceEditor editor;

	private IPositionUpdater positionsUpdater;

	public WikiContentOutlinePage(IDocumentProvider provider,
			WikiSourceEditor editor) {
		this.editor = editor;
	}

	public void createControl(Composite parent) {
		super.createControl(parent);
		TreeViewer tree = getTreeViewer();
		tree.setLabelProvider(new OutlineLabelProvider());
		tree.setContentProvider(new OutlineContentProvider());
		tree.setAutoExpandLevel(AbstractTreeViewer.ALL_LEVELS);
		tree.addSelectionChangedListener(this);

		IDocument document = editor.getDocument();

		positionsUpdater = new DefaultPositionUpdater(
				WikiTextParser.PositionCategory);
		document.addPositionUpdater(positionsUpdater);
		document.addDocumentPartitioningListener(this);

		WikiTextParser parser = new WikiTextParser(document);
		WikiSection section = parser.parse();
		getTreeViewer().setInput(section);
	}

	public void selectionChanged(SelectionChangedEvent event) {
		if (event.getSelection() instanceof IStructuredSelection) {
			IStructuredSelection selection = (IStructuredSelection) event
					.getSelection();
			Object obj = selection.getFirstElement();
			if (obj instanceof WikiSection) {
				WikiSection section = (WikiSection) obj;
				editor
						.selectAndReveal(section.getOffset(), section
								.getLength());
			}
		}
	}

	public void setWiki(WikiSection section) {
		getTreeViewer().setInput(section);
	}

	public void dispose() {
		super.dispose();
		editor.outlinePageClosed();
		editor = null;
	}

	public void documentPartitioningChanged(
			DocumentPartitioningChangedEvent event) {
		WikiTextParser parser = new WikiTextParser(event.getDocument());
		WikiSection section = parser.parse();
		getTreeViewer().setInput(section);
	}

	public void documentPartitioningChanged(IDocument document) {
	}

	// ////////////////////////////////////////////////////////////

	private static class OutlineContentProvider implements
			ITreeContentProvider, IStructuredContentProvider {

		public Object[] getChildren(Object parentElement) {
			return ((WikiSection) parentElement).getChildren().toArray();
		}

		public Object getParent(Object element) {
			return ((WikiSection) element).getParent();
		}

		public boolean hasChildren(Object element) {
			Object[] children = getChildren(element);
			return children != null && children.length != 0;
		}

		public Object[] getElements(Object inputElement) {
			return getChildren(inputElement);
		}

		public void dispose() {
			// do nothing
		}

		public void inputChanged(Viewer viewer, Object oldInput, Object newInput) {
		}
	}

	private static class OutlineLabelProvider extends LabelProvider {

		public String getText(Object element) {
			return ((WikiSection) element).getName();
		}

		public Image getImage(Object element) {
			if (element instanceof WikiSection)
				return Images.get(Images.STEP);
			return super.getImage(element);
		}
	}
}
