/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import java.util.logging.Level;
import java.util.logging.Logger;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.model.PageVersion;

/**
 * @author ivan
 *
 */
public class DeletePageVersionAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public DeletePageVersionAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Delete Latest Version");
		setImageDescriptor(Images.getDescriptor(Images.DELETE_PAGE));
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null
				&& MessageDialog.openConfirm(viewer.getControl().getShell(), 
						Labels.getText("deletePageVersion.confirm.title"), 
						Labels.getText("deletePageVersion.confirm.message")))
		{
			
			PageVersion version2Delete = page.getLatestVersion();
			if(version2Delete != null) {
				page.getServer().deletePageVersion(page, version2Delete.getVersion());
				try {
					closeOpenEditor(page);
				}catch (Exception e) {
					Logger.getLogger(getClass().getName()).log(Level.SEVERE, "Error closing editor", e);
				}
			}
		}
	}

	
}
