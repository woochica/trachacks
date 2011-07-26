/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class AddServerAction extends EditServerAction {

	public AddServerAction(StructuredViewer viewer) {
		super(viewer);
        setText( "Add New Server" );
        setImageDescriptor(Images.getDescriptor(Images.ADD_NEW_SERVER)); 
	}

	@Override
	protected ServerDetails getServerDetails() {
		return new ServerDetails();
	}
	
}
