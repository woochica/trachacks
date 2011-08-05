/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.compare.CompareEditorInput;
import org.eclipse.compare.CompareUI;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.comparation.ComparationFactory;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;

/**
 * @author ivan
 *
 */
public class MergePageAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public MergePageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Merge with latest");
		//setImageDescriptor(Images.getDescriptor(Images.ERROR)); // XXX
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null) {
			closeOpenEditor(page);
			CompareEditorInput editorInput = ComparationFactory.getMergeWithLatestCompareInput(page);
			CompareUI.openCompareEditor(editorInput);		
		}
	}
	
}
