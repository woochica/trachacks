/**
 * 
 */
package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.server.NewTracServer;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.eclipse.swt.widgets.Display;

/**
 * @author Matteo Merli
 * 
 */
public class TracServerActionProvider implements IActionsProvider
{
    private StructuredViewer viewer;
    
    private Action           connectAction;
    private Action           disconnectAction;
    private Action           editAction;
    private Action           deleteAction;
    
    private Action           createPageAction;
    
    public TracServerActionProvider( StructuredViewer viewer )
    {
        this.viewer = viewer;
        
        makeActions();
    }
    
    private void makeActions()
    {
        connectAction = new Action() {
            public void run()
            {
                if ( !viewer.getSelection().isEmpty() )
                {
                    TracServer server = (TracServer) ((IStructuredSelection) viewer
                            .getSelection()).getFirstElement();
                    
                    Display.getDefault().asyncExec( new ServerExecutor( server ) {
                        public void run()
                        {
                            this.server.connect();
                        }
                    } );
                    
                }
            }
        };
        connectAction.setText( "Connect to server" );
        
        disconnectAction = new Action() {
            public void run()
            {
                if ( !viewer.getSelection().isEmpty() )
                {
                    TracServer server = (TracServer) ((IStructuredSelection) viewer
                            .getSelection()).getFirstElement();
                    Display.getDefault().asyncExec( new ServerExecutor( server ) {
                        public void run()
                        {
                            this.server.disconnect();
                        }
                    } );
                }
            }
        };
        disconnectAction.setText( "Disconnect from server" );
        
        editAction = new Action() {
            @Override
            public void run()
            {
                if ( viewer.getSelection().isEmpty() )
                    return;
                
                TracServer server = (TracServer) ((IStructuredSelection) viewer
                        .getSelection()).getFirstElement();
                
                // Create the wizard
                WizardDialog dialog = new WizardDialog( viewer.getControl().getShell(),
                                                        new NewTracServer( server ) );
                dialog.open();
            }
        };
        
        editAction.setText( "Modify server settings" );
        
        deleteAction = new Action() {
            @Override
            public void run()
            {
                if ( !viewer.getSelection().isEmpty() )
                {
                    TracServer server = (TracServer) ((IStructuredSelection) viewer
                            .getSelection()).getFirstElement();
                    
                    // Open a dialog and ask to confirm
                    boolean res = MessageDialog
                            .openQuestion( viewer.getControl().getShell(),
                                           "Confirm Trac server deletion",
                                           "Are you sure to delete the '"
                                                   + server.getName()
                                                   + "' server configuration?" );
                    
                    if ( res != true )
                        return;
                    
                    TracServerList.getInstance().removeServer( server );
                    
                    Log.info( "Deleted Server " + server.getName() );
                }
                
            }
        };
        
        deleteAction.setText( "Delete the Trac Server Setting" );
        
        createPageAction = new CreatePage( viewer );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.views.actions.IActionsProvider#fillMenu(org.eclipse.jface.action.IMenuManager,
     *      org.eclipse.jface.viewers.IStructuredSelection)
     */
    public void fillMenu( IMenuManager menu, IStructuredSelection selection )
    {
        if ( selection.size() != 1 )
            return;
        
        if ( selection.getFirstElement() instanceof TracServer )
        {
            TracServer server = (TracServer) selection.getFirstElement();
            
            connectAction.setEnabled( !server.isConnected() );
            disconnectAction.setEnabled( server.isConnected() );
            createPageAction.setEnabled( server.isConnected() );
            
            // TODO: Enable create page action
            // menu.add( createPageAction );
            // menu.add( new Separator() );
            menu.add( connectAction );
            menu.add( disconnectAction );
            menu.add( new Separator() );
            menu.add( editAction );
            menu.add( deleteAction );
        }
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.views.actions.IActionsProvider#doubleClick(org.eclipse.jface.viewers.IStructuredSelection)
     */
    public void doubleClick( IStructuredSelection selection )
    {}
    
    private static abstract class ServerExecutor implements Runnable
    {
        TracServer server;
        
        public ServerExecutor( TracServer server )
        {
            this.server = server;
        }
        
    }
    
}
