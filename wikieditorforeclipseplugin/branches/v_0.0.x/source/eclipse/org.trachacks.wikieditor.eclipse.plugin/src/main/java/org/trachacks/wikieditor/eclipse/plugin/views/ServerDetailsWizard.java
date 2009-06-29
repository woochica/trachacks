/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views;

import java.net.MalformedURLException;
import java.net.URL;

import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.events.SelectionListener;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.model.ServerList;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelCheckField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelPasswordField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelTextField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.ValidationUtils;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class ServerDetailsWizard  extends Wizard implements INewWizard{

	private ServerDetailsWizardPage serverDetailsPage;
    
	/**
	 * @param serverDetails
	 */
	public ServerDetailsWizard(ServerDetails serverDetails) {
		super();
		serverDetailsPage = new ServerDetailsWizardPage(serverDetails);
	}

	@Override
	public void addPages() {
		super.addPages();
		addPage(serverDetailsPage);
	}


	@Override
	public boolean performFinish() {
		ServerDetails serverDetails = serverDetailsPage.getServerDetails();
		if(serverDetails.getId() != null) {
			ServerList.getInstance().updateServerDetails(serverDetails);
		}
		else {
			ServerList.getInstance().addServer(serverDetails);
		}
		return true;
	}

	
	public void init(IWorkbench workbench, IStructuredSelection selection) {
	}

}

class  ServerDetailsWizardPage extends WizardPage implements ModifyListener {

	private ServerDetails serverDetails;
	
    private LabelTextField serverName;
	private LabelTextField serverUrl;
	private LabelTextField username;
	private LabelTextField password;
	private LabelCheckField storeCredentials;

	private Button validateButton;
	
	protected ServerDetailsWizardPage(ServerDetails serverDetails) {
		super("serverDetailsWizardPage"); //$NON-NLS-1$
		this.serverDetails = (serverDetails != null ? serverDetails : new ServerDetails());
        setImageDescriptor(Images.getDescriptor(Images.TRAC_48));
        if(serverDetails.isNew()) {
            setTitle(Labels.getText("serverDetailsWizard.newServer.title")); //$NON-NLS-1$
            setDescription(Labels.getText("serverDetailsWizard.newServer.message")); //$NON-NLS-1$
        } else {
	        setTitle(Labels.getText("serverDetailsWizard.editServer.title")); //$NON-NLS-1$
	        setDescription(Labels.getText("serverDetailsWizard.editServer.message")); //$NON-NLS-1$
        }
        setPageComplete(false);
	}

	public void modifyText(ModifyEvent e) {
		if(validateServerDetails()) {
			validateButton.setEnabled(true);
			validateButton.setText(Labels.getText("serverDetailsWizard.validateConnection")); //$NON-NLS-1$
			setErrorMessage(null);
			setMessage(null);
			setPageComplete(true);
		}
		else {
			setErrorMessage(Labels.getText("serverDetailsWizard.serverDetails.notValid")); //$NON-NLS-1$
			validateButton.setEnabled(false);
			setPageComplete(false);
		}
	}

	public void createControl(Composite parent) {
        Composite container = new Composite(parent, SWT.NULL);
        GridLayout layout = new GridLayout();
        container.setLayout(layout);
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
        
        serverName = new LabelTextField(container, serverDetails.getName(), "serverDetailsWizard.serverName" , true); //$NON-NLS-1$
        serverUrl = new LabelTextField(container, serverDetails.getUrl(), "serverDetailsWizard.serverURL", true); //$NON-NLS-1$
        username = new LabelTextField(container, serverDetails.getUsername(), "serverDetailsWizard.username"); //$NON-NLS-1$
        password = new LabelPasswordField(container, serverDetails.getPassword(), "serverDetailsWizard.password"); //$NON-NLS-1$
        storeCredentials = new LabelCheckField(container, serverDetails.isStoreCredentials(), "serverDetailsWizard.storeCredentials"); //$NON-NLS-1$
        
        validateButton = new Button(container, SWT.PUSH);
        validateButton.setText(Labels.getText("serverDetailsWizard.validateConnection")); //$NON-NLS-1$
        validateButton.setEnabled(validateServerDetails());
        validateButton.addSelectionListener( new SelectionListener() {
            public void widgetDefaultSelected(SelectionEvent e){}
            public void widgetSelected(SelectionEvent event) {
            	validateServerConnection();
            }
        });
		
        serverName.getText().addModifyListener(this);
		serverUrl.getText().addModifyListener(this);
		username.getText().addModifyListener(this);
		password.getText().addModifyListener(this);
		
		 setControl(container);
	}
	
	private boolean validateServerName() {
		if(getServerDetails().isNew()) {
			String name = serverName.getValue();
			for (Server server : ServerList.getInstance()) {
				if(name.equals(server.getServerDetails().getName())) {
					serverName.setInvalid(Labels.getText("serverDetailsWizard.serverName.nameInUse")); //$NON-NLS-1$
					return false;
				}
			}
		}
		return true;
	}
	
	private boolean validateServerDetails() {
		return ValidationUtils.validateRequired(serverName)
				& validateServerName()
				& ValidationUtils.validateURL(serverUrl)
				& ValidationUtils.validateRequired(serverUrl);
		
	}
	
	private void validateServerConnection(){
        	try {
        		if( !Server.testConnection(getServerDetails())) {
            		setErrorMessage(
            				Labels.getText("serverDetailsWizard.validateConnection.error") + ": " + //$NON-NLS-1$ //$NON-NLS-2$
            				Labels.getText("serverDetailsWizard.validateConnection.error.no-xmlrpc")); //$NON-NLS-1$
        		}
        		else {
        			setMessage(Labels.getText("serverDetailsWizard.validateConnection.success")); //$NON-NLS-1$
        		}
        	} catch (Exception e) {
        		setErrorMessage(
        				Labels.getText("serverDetailsWizard.validateConnection.error") + ": " + //$NON-NLS-1$ //$NON-NLS-2$
        				Labels.getText(e.getClass().getName()));
        	}			
	}
	
	public ServerDetails getServerDetails() {
		serverDetails.setName(serverName.getValue());
		try {
			serverDetails.setUrl(new URL(serverUrl.getValue()));
		} catch (MalformedURLException ignored) {}
		serverDetails.setUsername(username.getValue());
		serverDetails.setPassword(password.getValue());
		serverDetails.setStoreCredentials(storeCredentials.getValueAsBoolean());
		return serverDetails;
	}
}
