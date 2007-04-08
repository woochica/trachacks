package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;

public class WikiPageActionsProvider implements IActionsProvider
{
    
    private StructuredViewer viewer;
    
    private Action           actionCommitPage;
    
    private Action           actionOpenEditor;
    
    private Action		     actionCreatePage;
    
    public WikiPageActionsProvider( StructuredViewer viewer )
    {
        this.viewer = viewer;
        
        makeActions();
    }
    
    private void makeActions()
    {
        actionOpenEditor = new OpenEditor( viewer );
        actionCommitPage = new CommitPage( viewer );
        actionCreatePage = new CreatePage( viewer );
    }
    
    public void fillMenu( IMenuManager menu, IStructuredSelection selection )
    {
        if ( selection.size() != 1 )
            return;
        
        if ( selection.getFirstElement() instanceof WikiPage )
        {
            WikiPage page = (WikiPage) selection.getFirstElement();
            
            actionOpenEditor.setEnabled( page.exists() && !page.isRoot() );
            actionCommitPage.setEnabled( page.exists() && page.isDirty() );
            actionCreatePage.setEnabled( true );
            
            menu.add( actionOpenEditor );
            menu.add( actionCommitPage );
            // menu.add( new Separator() );
            // menu.add( actionCreatePage );
        }
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.views.actions.IActionsProvider#doubleClick(org.eclipse.jface.viewers.IStructuredSelection)
     */
    public void doubleClick( IStructuredSelection selection )
    {
        if ( selection.size() != 1 )
            return;
        
        if ( selection.getFirstElement() instanceof WikiPage )
        {
            WikiPage page = (WikiPage) selection.getFirstElement();
            if ( page.exists() && !page.isRoot() )
            {
                actionOpenEditor.run();
            }
        }
    }
    
}
