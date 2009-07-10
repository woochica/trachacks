/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.SWT;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractLongRunningBaseAction;

/**
 * @author ivan
 *
 */
public class RefreshSelectionAction extends AbstractLongRunningBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public RefreshSelectionAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Refresh");
		setImageDescriptor(Images.getDescriptor(Images.REFRESH));
		setAccelerator(SWT.F5);
	}

	@Override
	public void runInternal() {
		Server server = getSingleSelection(viewer, Server.class);
		if(server != null) {
			server.refresh();
		}
	}
}
