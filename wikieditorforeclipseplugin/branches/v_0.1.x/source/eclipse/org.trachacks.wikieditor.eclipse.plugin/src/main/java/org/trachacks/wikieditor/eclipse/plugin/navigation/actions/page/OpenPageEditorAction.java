/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.SWT;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.ide.IDE;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiEditor;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiPageEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;

/**
 * @author ivan
 *
 */
public class OpenPageEditorAction extends AbstractBaseAction {

    private StructuredViewer viewer;
    
    public OpenPageEditorAction(StructuredViewer viewer) {
        this.viewer = viewer;
        setText( "Open" );
        setToolTipText( "Open wiki page in editor." );
        setAccelerator( SWT.F3 );
    }
	
	@Override
	public void runInternal() throws PartInitException {

		Page page = getSingleSelection(viewer, Page.class);
        if (page != null) {

        	WikiPageEditorInput wikiEditorInput = new WikiPageEditorInput(page);
			IWorkbenchWindow window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
			IWorkbenchPage workbenchPage = window.getActivePage();
			
			
	
			IDE.openEditor(workbenchPage, wikiEditorInput, WikiEditor.class.getName());

		} 
	}
}
