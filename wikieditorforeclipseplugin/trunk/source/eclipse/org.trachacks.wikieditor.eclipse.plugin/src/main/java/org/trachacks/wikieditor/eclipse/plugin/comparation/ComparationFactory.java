/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.comparation;

import java.lang.reflect.InvocationTargetException;

import org.eclipse.compare.CompareConfiguration;
import org.eclipse.compare.CompareEditorInput;
import org.eclipse.compare.structuremergeviewer.Differencer;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.PlatformUI;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.model.PageVersion;

/**
 * @author ivan
 * 
 */
public class ComparationFactory{


	public static CompareEditorInput getMergeWithLatestCompareInput(final Page page) {
		final PageVersion baseVersion = page.getBaseVersion();
		final PageVersion latestVersion = page.getLatestVersion();

		CompareConfiguration configuration = new CompareConfiguration();
		configuration.setLeftEditable(true);
		
		CompareEditorInput mergeEditorInput = new CompareEditorInput(configuration) {

			private PageInput left = new PageInput(baseVersion);

			/* (non-Javadoc)
			 * @see org.eclipse.compare.CompareEditorInput#saveChanges(org.eclipse.core.runtime.IProgressMonitor)
			 */
			@Override
			public void saveChanges(IProgressMonitor monitor) throws CoreException {
				super.saveChanges(monitor);
				String mergedContent = left.getText();
				page.edit(mergedContent);

				if(MessageDialog.openConfirm(
						PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(), 
						Labels.getText("markAsMerged.confirm.title"),  //$NON-NLS-1$
						Labels.getText("markAsMerged.confirm.message"))) //$NON-NLS-1$
				{
					page.markAsMerged(latestVersion.getVersion());
					// close editor
					IEditorPart editor = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage().getActiveEditor();
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage().closeEditor(editor, true);
				}
			}
			
			

			@Override
			protected Object prepareInput(IProgressMonitor monitor) throws InvocationTargetException, InterruptedException {
				Differencer d = new Differencer();
				return d.findDifferences(false,  monitor, null, null, left, new PageVersionInput(latestVersion));
			}
			
		};
		
		mergeEditorInput.setTitle(page.getName() + " " + Labels.getText("mergeWithLatest.title"));  //$NON-NLS-1$ //$NON-NLS-2$
		
		return mergeEditorInput;
	}
}