/**
 * 
 */
package mm.eclipse.trac.views.actions;

import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
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
    private Action           deleteAction;
    
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
        
        deleteAction = new Action() {
        	@Override
        	public void run() {
                if ( !viewer.getSelection().isEmpty() )
                {
                    TracServer server = (TracServer) ((IStructuredSelection) viewer
                            .getSelection()).getFirstElement();
                    TracServerList.getInstance().removeServer(server);
                }
        		
        	}
        };
        
        deleteAction.setText("Delete the Trac Server Setting");
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
            
            menu.add( connectAction );
            menu.add( disconnectAction );
            menu.add( new Separator() );
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
