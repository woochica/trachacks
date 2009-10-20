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

/**
 * @author ivan
 *
 */
public class UneditPageAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public UneditPageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Unedit");
		//setImageDescriptor(Images.getDescriptor(Images.ERROR)); // XXX
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null 
				&& page.isEdited() 
				&& MessageDialog.openConfirm(viewer.getControl().getShell(), 
						Labels.getText("uneditPageVersion.confirm.title"), 
						Labels.getText("uneditPageVersion.confirm.message"))) 
		{
			page.unedit();
			
			try {
				closeOpenEditor(page);
			}catch (Exception e) {
				Logger.getLogger(getClass().getName()).log(Level.SEVERE, "Error closing editor", e);
			}
		}
	}
	
}
