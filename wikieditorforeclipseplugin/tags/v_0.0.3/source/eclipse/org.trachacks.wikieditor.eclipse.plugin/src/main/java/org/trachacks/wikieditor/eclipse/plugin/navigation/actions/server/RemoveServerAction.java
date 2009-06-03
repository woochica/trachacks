/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.model.ServerList;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public class RemoveServerAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public RemoveServerAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Delete");
		setImageDescriptor(Images.getDescriptor(Images.DELETE_SERVER));
	}
	
	@Override
	public void runInternal() {
		Server server = getSingleSelection(viewer, Server.class);
		if(server != null
				&& MessageDialog.openConfirm(viewer.getControl().getShell(), 
				Labels.getText("deleteServer.confirm.title"), 
				Labels.getText("deleteServer.confirm.message"))) 
		{
			ServerList.getInstance().removeServer(server.getServerDetails());
		}
		
	}
}
