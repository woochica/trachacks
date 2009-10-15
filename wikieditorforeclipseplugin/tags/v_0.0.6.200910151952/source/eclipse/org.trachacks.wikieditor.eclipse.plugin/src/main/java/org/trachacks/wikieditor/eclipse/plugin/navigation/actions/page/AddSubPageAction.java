/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.NewPageWizard;

/**
 * @author ivan
 *
 */
public class AddSubPageAction extends AbstractBaseAction {

    private StructuredViewer viewer;

    public AddSubPageAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
        setText( "Add wiki page" );
        setImageDescriptor(Images.getDescriptor(Images.ADD_NEW_PAGE));
	}

	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null) {
			Server server = page.getServer();
			if(server != null && server.isConnected()) {
				String parentFolder = null;
				if(page.getParent() != null || !page.getChildren().isEmpty()) {
					parentFolder =  page.getName();
				}
				
				new WizardDialog(
						viewer.getControl().getShell(),
						new NewPageWizard(server, parentFolder))
						.open();
			}
		}
	}
}
