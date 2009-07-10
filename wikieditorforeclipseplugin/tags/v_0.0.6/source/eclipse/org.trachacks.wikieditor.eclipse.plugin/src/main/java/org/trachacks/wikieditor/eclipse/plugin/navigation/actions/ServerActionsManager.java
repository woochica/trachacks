/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.AddPageAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.AddServerAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.ConnectServerAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.DisconnectServerAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.EditServerAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.RefreshSelectionAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.RemoveServerAction;

/**
 * @author ivan
 * 
 */
public class ServerActionsManager {

	private StructuredViewer viewer;
	
	private Action connect;
	private Action disconnect;
	private Action refreshSelection;
	private Action addPage;
	private Action deleteServer;
	private Action editServerDetails;
	private Action addServerDetails;
	
	/**
	 * @param viewer
	 */
	public ServerActionsManager(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		connect = new ConnectServerAction(viewer);
		disconnect = new DisconnectServerAction(viewer);
		refreshSelection = new RefreshSelectionAction(viewer);
		addPage = new AddPageAction(viewer);
		deleteServer = new RemoveServerAction(viewer);
		editServerDetails = new EditServerAction(viewer);
		addServerDetails = new AddServerAction(viewer);
	}



	public void fillMenu(IMenuManager menu, IStructuredSelection selection) {
		if (selection.size() == 1 && selection.getFirstElement() instanceof Server) {
			Server server = (Server) selection.getFirstElement();


			if(server.isConnected()) {
				menu.add(disconnect);
				menu.add(refreshSelection);
			} else {
				menu.add(connect);
			}
			menu.add(new Separator());
			menu.add(addPage);
			addPage.setEnabled(server.isConnected());
			menu.add(deleteServer);
			menu.add(new Separator());
			menu.add(editServerDetails);
		}
	}
	
	public void fillToolBar(IToolBarManager toolBarManager) {
		toolBarManager.add(addServerDetails);
		//toolBarManager.add(addPage);
	}
	
	 public void doubleClick(IStructuredSelection selection) {
			if (selection.size() == 1 && selection.getFirstElement() instanceof Server) {
				Server server = (Server) selection.getFirstElement();
				if(server.isConnected()) {
					editServerDetails.run();
				}
				else {
					connect.run();
				}
			}
	 }
}
