/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import java.lang.reflect.InvocationTargetException;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.dialogs.ProgressMonitorDialog;
import org.eclipse.jface.operation.IRunnableWithProgress;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.PlatformUI;
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

			dialog.run(false, true, new IRunnableWithProgress() {
				public void run(IProgressMonitor monitor) {
					monitor.beginTask("Running " + getText() + " ...", IProgressMonitor.UNKNOWN);
					try {
						/** Run Internal */
						AbstractLongRunningBaseAction.this.runInternal();
						
					} catch (Throwable e) {
						Logger.getAnonymousLogger().log(Level.WARNING, e.getMessage(), e);
						MessageDialog.openError(shell, 
								"Error performing action \"" + getText() + "\"", 
								Labels.getText(e.getClass().getName()));
					}finally {
						monitor.done();
					}
				}
			});
			
		} catch (InvocationTargetException e) {
			e.printStackTrace();
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}

}
