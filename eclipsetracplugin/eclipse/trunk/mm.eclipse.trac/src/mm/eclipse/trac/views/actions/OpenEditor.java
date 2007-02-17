/**
 * 
 */
package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.editors.WikiEditorInput;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.viewers.DoubleClickEvent;
import org.eclipse.jface.viewers.IDoubleClickListener;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.ide.IDE;

/**
 * @author Matteo Merli
 * 
 */
public class OpenEditor extends Action implements IDoubleClickListener
{
    TreeViewer viewer;
    
    public OpenEditor( TreeViewer viewer )
    {
        this.viewer = viewer;
        setText( "Open" );
        setToolTipText( "Open wiki page in editor." );
        viewer.addDoubleClickListener( this );
    }
    
    public void doubleClick( DoubleClickEvent event )
    {
        run();
    }
    
    public void run()
    {
        ISelection selection = viewer.getSelection();
        Object obj = ((IStructuredSelection) selection).getFirstElement();
        
        if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            Log.info( "Opening: " + page );
            
            WikiEditorInput wikiEditorInput = new WikiEditorInput( page );
            
            IWorkbenchWindow window = PlatformUI.getWorkbench()
                    .getActiveWorkbenchWindow();
            IWorkbenchPage workbenchPage = window.getActivePage();
            
            try
            {
                IDE.openEditor( workbenchPage, wikiEditorInput,
                        "mm.eclipse.trac.editors.WikiEditor" );
            } catch ( PartInitException e )
            {
                Log.error( "Error opening wiki editor.", e );
                return;
            }
            
        } else
        {
            Log.error( "Unknown resource: " + obj );
        }
    }
}
