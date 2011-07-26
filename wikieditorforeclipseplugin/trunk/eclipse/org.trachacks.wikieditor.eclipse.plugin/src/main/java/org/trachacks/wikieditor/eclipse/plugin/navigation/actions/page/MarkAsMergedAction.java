/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.model.PageVersion;

/**
 * @author ivan
 *
 */
public class MarkAsMergedAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public MarkAsMergedAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Mark as merged");
		//setImageDescriptor(Images.getDescriptor(Images.ERROR)); // XXX
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null) {
			PageVersion merginVersion = page.getLatestVersion();
			if(merginVersion != null
					&& MessageDialog.openConfirm(viewer.getControl().getShell(), 
							Labels.getText("markAsMerged.confirm.title"), 
							Labels.getText("markAsMerged.confirm.message")))
			{
				page.markAsMerged(merginVersion.getVersion());
			}
		}
	}
	
}
