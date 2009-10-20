/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import java.util.logging.Level;
import java.util.logging.Logger;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.part.FileEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.Activator;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiPageEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public class DeletePageAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public DeletePageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Delete");
		setImageDescriptor(Images.getDescriptor(Images.DELETE_PAGE));
	}
	
	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null
				&& MessageDialog.openConfirm(viewer.getControl().getShell(), 
						Labels.getText("deletePage.confirm.title"), 
						Labels.getText("deletePage.confirm.message")))
		{
			
			page.getServer().deletePage(page);
			
			try {
				closeOpenEditor(page);
			}catch (Exception e) {
				Logger.getLogger(getClass().getName()).log(Level.SEVERE, "Error closing editor", e);
			}
		}
	}

	
}
