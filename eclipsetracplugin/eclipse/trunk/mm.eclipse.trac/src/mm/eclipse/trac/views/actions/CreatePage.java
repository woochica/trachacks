package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.Images;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.WikiPage;
import mm.eclipse.trac.wiki.NewWikiPage;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;

public class CreatePage extends Action
{
    private final StructuredViewer viewer;
    
    public CreatePage( StructuredViewer viewer )
    {
        this.viewer = viewer;
        setText( "Create wiki page" );
        setToolTipText( "Create a new Wiki page" );
        setImageDescriptor( Images.getDescriptor( Images.CreatePage ) );
    }
    
    @Override
    public void run()
    {
        ISelection selection = viewer.getSelection();
        Object obj = ((IStructuredSelection) selection).getFirstElement();
        
        TracServer tracServer;
        WikiPage wikiPage;
        
        if ( obj instanceof WikiPage ) {
            wikiPage = (WikiPage) obj;
            tracServer = wikiPage.getServer();
        }
        else if ( obj instanceof TracServer ) {
            wikiPage = null;
            tracServer = (TracServer) obj;
        }
        else
            return;
        
        WizardDialog dialog = new WizardDialog( viewer.getControl().getShell(),
                new NewWikiPage( tracServer, wikiPage ) );
        dialog.open();
        
    }
    
    @Override
    public boolean isEnabled()
    {
        return true;
    }
}
