/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.NewPageWizard;

/**
 * @author ivan
 *
 */
public class AddPageAction extends AbstractBaseAction {

    private StructuredViewer viewer;

    public AddPageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
        setText( "Add wiki page" );
        setImageDescriptor(Images.getDescriptor(Images.ADD_NEW_PAGE));
	}

	@Override
	public void runInternal() {
		Server server = getSingleSelection(viewer, Server.class);
		if(server != null && server.isConnected()) {
			new WizardDialog(
					viewer.getControl().getShell(),
					new NewPageWizard(server))
					.open();
		}
	}
}
