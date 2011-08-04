/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.compare.CompareConfiguration;
import org.eclipse.compare.CompareUI;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.comparation.ComparationFactory;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.CommitPageWizard;

/**
 * @author ivan
 *
 */
public class CommitPageAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public CommitPageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Commit Changes");
		setImageDescriptor(Images.getDescriptor(Images.COMMIT_PAGE));
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null) {
			new WizardDialog(viewer.getControl().getShell(),
					new CommitPageWizard(page)).open();
		}
	}
}
