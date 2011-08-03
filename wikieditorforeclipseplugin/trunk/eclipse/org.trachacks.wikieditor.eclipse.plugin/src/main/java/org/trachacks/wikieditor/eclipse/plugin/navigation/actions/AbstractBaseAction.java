/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import org.eclipse.core.runtime.Status;
import org.eclipse.jface.action.Action;
import org.eclipse.jface.dialogs.ErrorDialog;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.trachacks.wikieditor.eclipse.plugin.Activator;
import org.trachacks.wikieditor.eclipse.plugin.Logger;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public abstract class AbstractBaseAction extends Action {

	protected abstract void runInternal() throws Exception; 
	
	@Override
	public void run() {
		try {
			runInternal();
		} catch (Throwable e) {
			Logger.error(e.getMessage(), e);
			showErrorMessage(e);
		}
	}
	
	protected <T> T getSingleSelection(StructuredViewer viewer, Class<T> requiredClass) {
		IStructuredSelection selection = (IStructuredSelection) viewer.getSelection();
		if(selection.size() == 1 && requiredClass.isInstance(selection.getFirstElement())) {
			return (T) selection.getFirstElement();
		}
		return null;
	}
	
	/*
	 * This way of closing open editor  doesn't look too right but it seems to work...
	 * @param page
	 */
	protected void closeOpenEditor(Page page) {
		WikiEditorInput editorInput = new WikiEditorInput(page);
		IWorkbenchWindow[] windows = PlatformUI.getWorkbench().getWorkbenchWindows();
		for (int j = 0; j < windows.length; j++) {
			IWorkbenchWindow workbenchWindow = windows[j];
			IWorkbenchPage[] pages = workbenchWindow.getPages();
			for (int i = 0; i < pages.length; i++) {
				IEditorPart editorPart = pages[i].findEditor(editorInput);
				pages[i].closeEditor(editorPart, true);
			}
		}
	}
	
	protected void showErrorMessage(Throwable e) {
		String exceptionName = e.getClass().getName();
		if(Labels.containsKey(exceptionName)) {
			MessageDialog.openError(new Shell(), 
					"Error performing action \"" + getText() + "\"", 
					Labels.getText(e.getClass().getName()));
		} else {
			final Shell shell = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell();
			String message = "Error performing action \"" + getText() + "\"";
			ErrorDialog.openError(
					shell,	message, message,
					new Status(Status.ERROR, Activator.PLUGIN_ID, e.getMessage(), e)
					);
		}
	}
}
