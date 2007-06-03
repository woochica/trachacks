package mm.eclipse.trac.server;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;

import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchWizard;

/**
 * This is a sample new wizard. Its role is to create a new file resource in the
 * provided container. If the container resource (a folder or a project) is
 * selected in the workspace when the wizard is opened, it will accept it as the
 * target container. The wizard creates one file with the extension "mpe". If a
 * sample multi-page editor (also available as a template) is registered for the
 * same extension, it will be able to open it.
 */

public class NewTracServer extends Wizard implements INewWizard
{
    private NewTracServerPage page;
    private TracServer        server;
    
    /**
     * Constructor for NewTracServer.
     */
    public NewTracServer()
    {
        this( null );
    }
    
    public NewTracServer( TracServer tracServer )
    {
        super();
        setNeedsProgressMonitor( true );
        this.server = tracServer;
    }
    
    /**
     * Adding the page to the wizard.
     */
    
    public void addPages()
    {
        page = new NewTracServerPage( server );
        addPage( page );
    }
    
    /**
     * This method is called when 'Finish' button is pressed in the wizard. We
     * will create an operation and run it using wizard as execution context.
     */
    public boolean performFinish()
    {
        Log.info( "Adding server..." );
        TracServerList.getInstance().addServer( page.getTracServer() );
        Log.info( "OK" );
        return true;
    }
    
    /**
     * We will accept the selection in the workbench to see if we can initialize
     * from it.
     * 
     * @see IWorkbenchWizard#init(IWorkbench, IStructuredSelection)
     */
    public void init( IWorkbench workbench, IStructuredSelection selection )
    {}
}
