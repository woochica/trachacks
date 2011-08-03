/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import java.lang.reflect.InvocationTargetException;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.dialogs.ProgressMonitorDialog;
import org.eclipse.jface.operation.IRunnableWithProgress;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.PlatformUI;
import org.trachacks.wikieditor.eclipse.plugin.Logger;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public abstract class AbstractLongRunningBaseAction extends AbstractBaseAction {

	@Override
	public void run() {
		final Shell shell = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell();
		ProgressMonitorDialog dialog = new ProgressMonitorDialog(shell);
		try {

			dialog.run(false, false, new IRunnableWithProgress() {
				public void run(IProgressMonitor monitor) {
					monitor.beginTask("Running " + getText() + " ...", IProgressMonitor.UNKNOWN);
					try {
						monitor.worked(IProgressMonitor.UNKNOWN);
						/** Run Internal */
						AbstractLongRunningBaseAction.this.runInternal();
						
					} catch (Throwable e) {
						Logger.error(e.getMessage(), e);
						showErrorMessage(e);
					}finally {
						monitor.done();
					}
				}
			});
			
		} catch (InvocationTargetException e) {
			Logger.error(e.getMessage(), e);
		} catch (InterruptedException e) {
			Logger.error(e.getMessage(), e);
		}
	}

}
