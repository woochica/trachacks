/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Shell;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractLongRunningBaseAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelPasswordField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelTextField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public class ConnectServerAction extends AbstractLongRunningBaseAction {

    private StructuredViewer viewer;
    
	/**
	 * 
	 */
	public ConnectServerAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
        setText( "Connect Server" );
        setImageDescriptor(Images.getDescriptor(Images.SERVER_CONNECTED));
	}

	@Override
	public void runInternal() {
		Server server = getSingleSelection(viewer, Server.class);
		if(server != null) {
			if(server.getServerDetails().isStoreCredentials()) {
				server.connect();
			}
			else {
				LoginWindow loginDialog = new LoginWindow(viewer.getControl().getShell(), server.getServerDetails().getName());
				loginDialog.open();
				if(loginDialog.getReturnCode() == Dialog.OK) {
					String username = loginDialog.username;
					String password = loginDialog.password;
					server.connect(username, password);
				}
			}
		}
	}
}
class LoginWindow extends Dialog {

	String username;
	String password;
	private String serverName;
	private LabelTextField usernameField;
	private LabelTextField passwordField;

	protected LoginWindow(Shell parentShell, String serverName) {
		super(parentShell);
		this.serverName = serverName;
		this.setBlockOnOpen(true);
	}

	protected void configureShell(Shell shell) {
		super.configureShell(shell);
		shell.setText(Labels.getText("loginWindow.title") + ": " + serverName);
		shell.setImage(Images.get(Images.TRAC_16));
	}

	
	@Override
	protected Control createDialogArea(Composite parent) {
		Composite composite = new Composite(parent, 0);
		GridLayout layout = new GridLayout();
		composite.setLayout(layout);
		composite.setLayoutData(new GridData(GridData.FILL_BOTH));
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
		layout.marginWidth = 10;        
		
		usernameField = new LabelTextField(composite, null, "loginWindow.username");
		passwordField = new LabelPasswordField(composite, null, "loginWindow.password");
		
		return composite;
	}



	@Override
	protected void okPressed() {
		username = usernameField.getValue();
		password = passwordField.getValue();
		super.okPressed();
	}

	
	
}
