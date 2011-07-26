/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;

/**
 * @author ivan
 *
 */
public class DisconnectServerAction extends AbstractBaseAction {

    private StructuredViewer viewer;
	/**
	 * 
	 */
	public DisconnectServerAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
        setText( "Disconnect Server" );
        setImageDescriptor(Images.getDescriptor(Images.SERVER_DISCONNECTED));
	}
	
	@Override
	public void runInternal() {
		Server server = getSingleSelection(viewer, Server.class);
		if(server != null) {
			server.disconnect();
		}
	}
}
