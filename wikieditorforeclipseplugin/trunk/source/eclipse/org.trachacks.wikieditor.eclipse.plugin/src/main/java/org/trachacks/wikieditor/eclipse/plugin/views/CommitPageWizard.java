/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views;


import java.util.logging.Level;
import java.util.logging.Logger;

import org.apache.commons.lang.StringUtils;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelTextArea;
import org.trachacks.wikieditor.eclipse.plugin.views.util.LabelTextField;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;

/**
 * @author ivan
 *
 */
public class CommitPageWizard  extends Wizard implements INewWizard{

	private Page page = null;
	private CommitDetailsWizardPage commitDetailsPage;
//	private MergeConflictsWizardPage mergeConflictsPage;

	public CommitPageWizard(Page page) {
		this(page, false);
	}

	public CommitPageWizard(Page page, boolean force) {
		super();
		this.page = page;
		commitDetailsPage = new CommitDetailsWizardPage(page, force);
//		mergeConflictsPage = new MergeConflictsWizardPage(page);
		setNeedsProgressMonitor(true);
	}

	@Override
	public void addPages() {
		super.addPages();
//		addPage(mergeConflictsPage);
		addPage(commitDetailsPage);
	}


	@Override
	public boolean performFinish() {
		String comment = commitDetailsPage.comment.getValue();
		boolean isMinorEdit = StringUtils.isBlank(comment);
		Page page = commitDetailsPage.page; 
		try {
			page.commit(comment, isMinorEdit);
		} catch (ConcurrentEditException e) {
			Logger.getAnonymousLogger().log(Level.INFO, e.getMessage(), e);
			MessageDialog.openError(getShell(), 
					Labels.getText("commitPageWizard.concurrentEditError.title"),  //$NON-NLS-1$
					Labels.getText("commitPageWizard.concurrentEditError.message")); //$NON-NLS-1$
			commitDetailsPage.setPageComplete(false);
			return false;
		} catch (PageNotModifiedException e) {
			MessageDialog.openInformation(getShell(),
					Labels.getText("commitPageWizard.pageNotModified.title"),  //$NON-NLS-1$
					Labels.getText("commitPageWizard.pageNotModified.message")); //$NON-NLS-1$
			page.unedit();
		}
		return true;
	}

	
	public void init(IWorkbench workbench, IStructuredSelection selection) {
	}

}

class  CommitDetailsWizardPage extends WizardPage implements ModifyListener {
	Page page;
	LabelTextField comment;
	
	protected CommitDetailsWizardPage(Page page, boolean force) {
		super("CommitPage"); //$NON-NLS-1$
		this.page = page;
        setImageDescriptor(Images.getDescriptor(Images.TRAC_48));
        setTitle(Labels.getText("commitPageWizard.title")); //$NON-NLS-1$
        setDescription(Labels.getText("commitPageWizard.message")); //$NON-NLS-1$
	}

	public void modifyText(ModifyEvent e) {
		// TODO Auto-generated method stub
		
	}

	public void createControl(Composite parent) {
        Composite container = new Composite(parent, SWT.NULL);
        GridLayout layout = new GridLayout();
        container.setLayout(layout);
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
		// TODO Auto-generated method stub
		comment = new LabelTextArea(container, "", "commitPageWizard.comment" , true); //$NON-NLS-1$ //$NON-NLS-2$
		
		setControl(container);
	}

}

/*
class MergeConflictsWizardPage  extends WizardPage implements ModifyListener {
	Page page;
	CompareEditorInput compareInput ;
	
	protected MergeConflictsWizardPage(Page page) {
		super("mergeConflictsPage");
		this.page = page;
        setImageDescriptor(Images.getDescriptor(Images.TRAC_48));
        setTitle("Merge Contents"); // FIXME literals
        setDescription("Merge conflicting contents before continue"); //FIXME literals		
	}

	public void modifyText(ModifyEvent e) {
		// TODO Auto-generated method stub
		
	}

	public void createControl(Composite parent) {
		compareInput =  ComparationFactory.getMergeWithLatestCompareInput(page);
		try {
			compareInput.run(new NullProgressMonitor());
		} catch(Exception ignored) {}
		Control control = compareInput.createContents(parent);
		setControl(control);
	}
	
}
*/