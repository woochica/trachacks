package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.dialogs.InputDialog;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.jface.window.Window;

public class CommitPage extends Action
{
    private static final String ImagePath = "icons/page-commit.gif";
    
    private final TreeViewer    viewer;
    
    public CommitPage( TreeViewer viewer )
    {
        this.viewer = viewer;
        setText( "Commit page" );
        setToolTipText( "Commit page in Trac database" );
        setImageDescriptor( Activator.getImageDescriptor( ImagePath ) );
    }
    
    @Override
    public void run()
    {
        ISelection selection = viewer.getSelection();
        Object obj = ((IStructuredSelection) selection).getFirstElement();
        
        if ( !(obj instanceof WikiPage) )
            return;
        
        WikiPage page = (WikiPage) obj;
        if ( !page.isDirty() )
            return;
        
        // Open a dialog to ask for a commit message
        InputDialog dialog = new InputDialog( viewer.getControl().getShell(),
                                              "Trac Page Commit Message",
                                              "Insert the commit message for page '"
                                                      + page.getFullName() + "'", null,
                                              null );
        dialog.setBlockOnOpen( true );
        
        if ( dialog.open() == Window.CANCEL )
            return;
        
        page.commit( dialog.getValue() );
        Log.info( "Committed page " + page );
    }
    
    @Override
    public boolean isEnabled()
    {
        if ( !viewer.getSelection().isEmpty() )
        {
            ISelection selection = viewer.getSelection();
            Object obj = ((IStructuredSelection) selection).getFirstElement();
            
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                Log.info( "Is Enabled for page " + page.getSimpleName() + " : "
                        + (page.isDirty() ? "True" : "False") );
                return page.isDirty();
            }
        }
        
        return false;
    }
    
}
