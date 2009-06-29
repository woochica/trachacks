package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.util.ResourceBundle;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.action.IAction;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.IVerticalRuler;
import org.eclipse.jface.text.source.SourceViewerConfiguration;
import org.eclipse.jface.text.source.projection.ProjectionSupport;
import org.eclipse.jface.text.source.projection.ProjectionViewer;
import org.eclipse.swt.custom.StyledText;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditor;
import org.eclipse.ui.texteditor.ContentAssistAction;
import org.eclipse.ui.texteditor.ITextEditorActionDefinitionIds;
import org.eclipse.ui.views.contentoutline.IContentOutlinePage;
import org.trachacks.wikieditor.eclipse.plugin.editor.model.WikiSection;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

public class WikiSourceEditor extends AbstractDecoratedTextEditor {
	private WikiContentOutlinePage contentOutline;

	private WikiSection section;

	private ProjectionSupport projectionSupport;

	// private WikiOccurrencesUpdater occurrencesUpdater;

	public WikiSourceEditor() {
		super();

		setDocumentProvider(new WikiDocumentProvider());
		SourceViewerConfiguration configuration = new WikiSourceViewerConfiguration(
				this, getSharedColors());
		setSourceViewerConfiguration(configuration);
	}

	public void createPartControl(Composite parent) {
		super.createPartControl(parent);
		/*
		 * ProjectionViewer projectionViewer = (ProjectionViewer)
		 * getSourceViewer(); projectionSupport = new ProjectionSupport(
		 * projectionViewer, getAnnotationAccess(), getSharedColors() );
		 * projectionSupport.install(); projectionViewer.doOperation(
		 * ProjectionViewer.TOGGLE );
		 * 
		 * occurrencesUpdater = new WikiOccurrencesUpdater( this );
		 */
		setWordWrap();
	}

	protected ISourceViewer createSourceViewer(Composite parent,
			IVerticalRuler ruler, int styles) {
		fAnnotationAccess = createAnnotationAccess();
		fOverviewRuler = createOverviewRuler(getSharedColors());

		ISourceViewer viewer = new ProjectionViewer(parent, ruler,
				fOverviewRuler, true, styles);
		// ensure decoration support has been created and configured:
		getSourceViewerDecorationSupport(viewer);

		return viewer;
	}

	protected void createActions() {
		super.createActions();
		IAction action = new ContentAssistAction(
				ResourceBundle.getBundle( this.getClass().getPackage().getName() + ".WikiEditorMessages" ), 
				"ContentAssistProposal.", this);
		action
				.setActionDefinitionId(ITextEditorActionDefinitionIds.CONTENT_ASSIST_PROPOSALS);
		setAction(WikiEditorContributor.CONTENTASSIST_ACTION, action);
		markAsStateDependentAction(WikiEditorContributor.CONTENTASSIST_ACTION,
				true);
	}

	private void setWordWrap() {
		if (getSourceViewer() != null) {
			StyledText text = getSourceViewer().getTextWidget();
			text.setWordWrap(true);
		}
	}

	public Object getAdapter(Class adapter) {
		if (IContentOutlinePage.class.equals(adapter)) {
			if (contentOutline == null)
				contentOutline = new WikiContentOutlinePage(
						getDocumentProvider(), this);
			return contentOutline;
		}

		if (projectionSupport != null) {
			Object adapt = projectionSupport.getAdapter(getSourceViewer(),
					adapter);
			if (adapter != null)
				return adapt;
		}

		return super.getAdapter(adapter);
	}

	@Override
	public void doSave(IProgressMonitor progressMonitor) {
		String content = getDocumentProvider().getDocument(getEditorInput()).get();

		Page page = (Page) getEditorInput().getAdapter(Page.class);
		page.edit(content);
		
		super.doSave(progressMonitor);
	}

	public IDocument getDocument() {
		IDocument doc = getDocumentProvider().getDocument(getEditorInput());
		return doc;
	}

	public WikiSection getSection() {
		return section;
	}

	public void setSection(WikiSection section) {
		this.section = section;
		if (contentOutline != null)
			contentOutline.setWiki(section);

		// if ( occurrencesUpdater != null )
		// occurrencesUpdater.update( getSourceViewer() );
	}

	public void outlinePageClosed() {
		contentOutline = null;
	}

}
