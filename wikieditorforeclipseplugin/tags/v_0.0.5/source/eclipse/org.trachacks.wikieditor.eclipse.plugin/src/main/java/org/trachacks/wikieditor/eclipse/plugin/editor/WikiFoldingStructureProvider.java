/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.Position;
import org.eclipse.jface.text.source.Annotation;
import org.eclipse.jface.text.source.projection.ProjectionAnnotation;
import org.eclipse.jface.text.source.projection.ProjectionAnnotationModel;
import org.trachacks.wikieditor.eclipse.plugin.editor.model.WikiSection;

public class WikiFoldingStructureProvider {

	private WikiSourceEditor editor;

	private IDocument document;

	private IProgressMonitor progressMonitor;

	public WikiFoldingStructureProvider(WikiSourceEditor editor) {
		this.editor = editor;
	}

	public void setProgressMonitor(IProgressMonitor progressMonitor) {
		this.progressMonitor = progressMonitor;
	}

	public void setDocument(IDocument document) {
		this.document = document;
	}

	public void updateFoldingRegions(WikiSection section) {
		try {

			ProjectionAnnotationModel model = (ProjectionAnnotationModel) editor
					.getAdapter(ProjectionAnnotationModel.class);
			if (model == null)
				return;

			Set<Position> currentRegions = new HashSet<Position>();
			addFoldingRegions(currentRegions, section.getChildren());
			updateFoldingRegions(model, currentRegions);
		} catch (BadLocationException e) {
			e.printStackTrace();
		}
	}

	private void updateFoldingRegions(ProjectionAnnotationModel model,
			Set<Position> currentRegions) {
		Annotation[] deletions = computeDifferences(model, currentRegions);

		Map<Annotation, Position> additionsMap = new HashMap<Annotation, Position>();
		for (Position pos : currentRegions)
			additionsMap.put(new ProjectionAnnotation(), pos);

		if ((deletions.length != 0 || additionsMap.size() != 0)
				&& (progressMonitor == null || !progressMonitor.isCanceled()))
			model.modifyAnnotations(deletions, additionsMap,
					new Annotation[] {});
	}

	private Annotation[] computeDifferences(ProjectionAnnotationModel model,
			Set<Position> current) {
		List<Annotation> deletions = new ArrayList<Annotation>();
		for (Iterator iter = model.getAnnotationIterator(); iter.hasNext();) {
			Object obj = iter.next();
			if (obj instanceof ProjectionAnnotation) {
				ProjectionAnnotation annotation = (ProjectionAnnotation) obj;
				Position position = model.getPosition((Annotation) annotation);
				if (current.contains(position))
					current.remove(position);
				else
					deletions.add(annotation);
			}
		}
		return (Annotation[]) deletions
				.toArray(new Annotation[deletions.size()]);
	}

	private void addFoldingRegions(Set<Position> regions, List<WikiSection> sections) throws BadLocationException {
		for (WikiSection section : sections) {
			if (section.getOffset() < 0)
				continue;

			int startLine = document.getLineOfOffset(section.getOffset());
			int endLine = document.getLineOfOffset(section.getOffset()
					+ section.getLength());
			if (startLine < endLine) {
				int start = document.getLineOffset(startLine);
				int end = document.getLineOffset(endLine)
						+ document.getLineLength(endLine);
				Position position = new Position(start, end - start);
				regions.add(position);
			}
			addFoldingRegions(regions, section.getChildren());
		}
	}
}
