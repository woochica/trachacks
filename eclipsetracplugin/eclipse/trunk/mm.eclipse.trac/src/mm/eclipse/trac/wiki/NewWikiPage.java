package mm.eclipse.trac.wiki;

import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchWizard;

public class NewWikiPage extends Wizard implements INewWizard
{
    
    private NewWikiPageWizard page;
    
    private TracServer        tracServer;
    private WikiPage          parentPage;
    
    /**
     * Constructor for NewTracServer.
     */
    public NewWikiPage( TracServer tracServer, WikiPage parentPage )
    {
        super();
        setNeedsProgressMonitor( true );
        this.tracServer = tracServer;
        this.parentPage = parentPage;
    }
    
    /**
     * Adding the page to the wizard.
     */
    
    public void addPages()
    {
        page = new NewWikiPageWizard( tracServer, parentPage );
        addPage( page );
    }
    
    /**
     * This method is called when 'Finish' button is pressed in the wizard. We
     * will create an operation and run it using wizard as execution context.
     */
    public boolean performFinish()
    {
        String serverName = page.getServerName();
        String pageName = page.getPageName();
        
        TracServer server = TracServerList.getInstance().getServerByName( serverName );
        WikiPage wikiPage = new WikiPage( server, pageName, 0, true, false );
        wikiPage.setDirty( true );
        
        // We now have to find the parent page, that can be different
        // from the one specified before.
        WikiPage current = server.getRootWikiPage();
        while ( true ) 
        {
            break;
        }
        
        return true;
    }
    
    /**
     * We will accept the selection in the workbench to see if we can initialize
     * from it.
     * 
     * @see IWorkbenchWizard#init(IWorkbench, IStructuredSelection)
     */
    public void init( IWorkbench workbench, IStructuredSelection selection )
    {
    }
    
}
