/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views;

import java.util.Arrays;
import java.util.List;

import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IViewPart;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.part.IShowInTarget;
import org.eclipse.ui.part.ShowInContext;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.NavigationPanel;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.OpenPageEditorAction;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelTextField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.eclipse.plugin.views.util.ValidationUtils;

/**
 * @author ivan
 *
 */
public class NewPageWizard  extends Wizard implements INewWizard {

	private Server server;
	private NewPageWizardPage newPageWizardPage;
	
	/**
	 * @param server
	 */
	public NewPageWizard(Server server) {
		this(server, null);
	}
	
	/**
	 * @param server
	 */
	public NewPageWizard(Server server, String parentFolder) {
		super();
		this.server = server;
		this.newPageWizardPage = new NewPageWizardPage(server.getPageNames(), parentFolder);
	}
	
	@Override
	public void addPages() {
		super.addPages();
		addPage(newPageWizardPage);
	}

	@Override
	public boolean performFinish() {
		String pageName = newPageWizardPage.getPageName();
		server.newPage(pageName);
		return true;
	}

	public void init(IWorkbench workbench, IStructuredSelection selection) {
	}

}
class  NewPageWizardPage extends WizardPage implements ModifyListener{

	private String parentFolder;
	private List<String> pageNames;
	private LabelTextField pageNameField;
	
	protected NewPageWizardPage(String[] pageNames, String parentFolder) {
		super("NewPageWizardPage"); //$NON-NLS-1$
		this.pageNames = Arrays.asList(pageNames);
		if(parentFolder != null) {
			this.parentFolder = parentFolder + "/";
		}
        setImageDescriptor(Images.getDescriptor(Images.TRAC_48));
        setTitle(Labels.getText("newPageWizard.pageName.title")); //$NON-NLS-1$
        setDescription(Labels.getText("newPageWizard.pageName.message")); //$NON-NLS-1$
		setPageComplete(false);
	}

	public void modifyText(ModifyEvent e) {
		if(validate()) {
			setPageComplete(true);
			setMessage(null);
			setErrorMessage(null);
		}
		else {
			setPageComplete(false);
			setErrorMessage(Labels.getText("newPageWizard.pageDetails.invalid")); //$NON-NLS-1$
		}
	}
	
	public boolean validate() {
		boolean required = ValidationUtils.validateRequired(pageNameField);
		if(required) {
			String pagename = pageNameField.getValue();
			if(pageNames.contains(pagename)) {
				setErrorMessage(Labels.getText("newPageWizard.pageName.inUse")); //$NON-NLS-1$
			}
			else {
				setErrorMessage(null);
				return true;
			}
		}
		return false;
	}

	public void createControl(Composite parent) {
        Composite container = new Composite(parent, SWT.NULL);
        GridLayout layout = new GridLayout();
        container.setLayout(layout);
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
        
        pageNameField = new LabelTextField(container,  parentFolder, "newPageWizard.pageName", true); //$NON-NLS-1$
        pageNameField.getText().addModifyListener(this);
        pageNameField.getText().selectAll();
        
        setControl(container);
	}
	
	public String getPageName() {
		return pageNameField.getValue();
	}
	
}
