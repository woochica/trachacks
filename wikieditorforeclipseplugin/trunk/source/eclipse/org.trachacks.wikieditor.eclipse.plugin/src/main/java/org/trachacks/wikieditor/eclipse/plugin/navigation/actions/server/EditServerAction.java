/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.compare.CompareConfiguration;
import org.eclipse.compare.CompareUI;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.comparation.ComparationFactory;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.ServerDetailsWizard;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class EditServerAction extends AbstractBaseAction {

    private StructuredViewer viewer;
	/**
	 * 
	 */
	public EditServerAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
        setText( "Edit server" );
        setImageDescriptor(Images.getDescriptor(Images.TEMPLATE)); //XXX
	}

	/* (non-Javadoc)
	 * @see org.eclipse.jface.action.Action#run()
	 */
	@Override
	public void runInternal() {

		ServerDetails serverDetails = getServerDetails();
		new WizardDialog(
				viewer.getControl().getShell(),
				new ServerDetailsWizard(serverDetails))
				.open();
		
	}

	protected ServerDetails getServerDetails() {
		ServerDetails serverDetails = null;
		IStructuredSelection selection = (IStructuredSelection) viewer.getSelection();
		if (selection.size() == 1 && selection.getFirstElement() instanceof Server) {
			serverDetails = ((Server)selection.getFirstElement()).getServerDetails();
		}
		else {
			serverDetails = new ServerDetails();
		}
		return serverDetails;
	}
	
	
}
