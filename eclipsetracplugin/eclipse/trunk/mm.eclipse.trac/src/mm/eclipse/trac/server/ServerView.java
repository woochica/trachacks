/**
 * 
 */
package mm.eclipse.trac.server;

import java.util.List;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Images;
import mm.eclipse.trac.models.ITracListener;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.util.DecoratingTableLabelProvider;
import mm.eclipse.trac.views.actions.TracServerActionProvider;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuListener;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.MenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.ITableLabelProvider;
import org.eclipse.jface.viewers.TableViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.jface.wizard.WizardDialog;
import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Menu;
import org.eclipse.swt.widgets.Table;
import org.eclipse.swt.widgets.TableColumn;
import org.eclipse.ui.IDecoratorManager;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.part.ViewPart;

/**
 * @author Matteo Merli
 * 
 */
public class ServerView extends ViewPart implements ITracListener
{
    private TableViewer              viewer;
    private Action                   newServerAction;
    
    private TracServerActionProvider serverActionProvider;
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.part.WorkbenchPart#createPartControl(org.eclipse.swt.widgets.Composite)
     */
    @Override
    public void createPartControl( Composite parent )
    {
        Table table = new Table( parent, SWT.SINGLE | SWT.H_SCROLL | SWT.V_SCROLL
                                         | SWT.FULL_SELECTION );
        table.setHeaderVisible( true );
        table.setLinesVisible( true );
        
        GridData layoutData = new GridData();
        layoutData.grabExcessHorizontalSpace = true;
        layoutData.grabExcessVerticalSpace = true;
        layoutData.horizontalAlignment = GridData.FILL;
        layoutData.verticalAlignment = GridData.FILL;
        table.setLayoutData( layoutData );
        
        TableColumn column = new TableColumn( table, SWT.LEFT, 0 );
        column.setWidth( 40 );
        
        column = new TableColumn( table, SWT.LEFT, 1 );
        column.setText( "Name" );
        column.setWidth( 300 );
        
        column = new TableColumn( table, SWT.LEFT, 2 );
        column.setText( "URL" );
        column.setWidth( 300 );
        
        viewer = new TableViewer( table );
        viewer.setContentProvider( new ServerContentProvider() );
        IDecoratorManager manager = Activator.getDefault().getWorkbench()
                .getDecoratorManager();
        viewer
                .setLabelProvider( new DecoratingTableLabelProvider(
                                                                     new ServerLabelProvider(),
                                                                     manager ) );
        viewer.setInput( TracServerList.getInstance().getServers() );
        TracServerList.getInstance().addListener( this );
        
        makeActions();
        hookContextMenu();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.part.WorkbenchPart#setFocus()
     */
    @Override
    public void setFocus()
    {
        viewer.getControl().setFocus();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.models.ITracListener#tracResourceModified(java.lang.Object)
     */
    public void tracResourceModified( Object resource )
    {
        if ( resource instanceof TracServerList )
        {
            TracServerList tracServerList = (TracServerList) resource;
            viewer.setInput( tracServerList.getServers() );
        }
    }
    
    private void makeActions()
    {
        newServerAction = new Action() {
            public void run()
            {
                // Create the wizard
                WizardDialog dialog = new WizardDialog( viewer.getControl().getShell(),
                                                        new NewTracServer() );
                dialog.open();
            }
        };
        newServerAction.setText( "Add a Trac server" );
        newServerAction.setImageDescriptor( Images.getDescriptor( Images.NewServer ) );
        
        IToolBarManager toolBarManager = getViewSite().getActionBars()
                .getToolBarManager();
        toolBarManager.add( newServerAction );
        
        IMenuManager menuManager = getViewSite().getActionBars().getMenuManager();
        menuManager.add( newServerAction );
        
        serverActionProvider = new TracServerActionProvider( viewer );
    }
    
    private void hookContextMenu()
    {
        MenuManager menuMgr = new MenuManager( "#PopupMenu" );
        menuMgr.setRemoveAllWhenShown( true );
        menuMgr.addMenuListener( new IMenuListener() {
            public void menuAboutToShow( IMenuManager manager )
            {
                ServerView.this.fillContextMenu( manager );
            }
        } );
        
        Menu menu = menuMgr.createContextMenu( viewer.getControl() );
        viewer.getControl().setMenu( menu );
        getSite().registerContextMenu( menuMgr, viewer );
    }
    
    private void fillContextMenu( IMenuManager manager )
    {
        manager.add( newServerAction );
        manager.add( new Separator() );
        serverActionProvider.fillMenu( manager, (IStructuredSelection) viewer
                .getSelection() );
        
        manager.add( new Separator( IWorkbenchActionConstants.MB_ADDITIONS ) );
    }
    
    // ////////////////////////////////////////////////////
    
    private static class ServerContentProvider implements IStructuredContentProvider
    {
        
        @SuppressWarnings("unchecked")
        public Object[] getElements( Object inputElement )
        {
            return ((List) inputElement).toArray();
        }
        
        public void dispose()
        {}
        
        public void inputChanged( Viewer viewer, Object oldInput, Object newInput )
        {}
        
    }
    
    private static class ServerLabelProvider implements ITableLabelProvider
    {
        
        public Image getColumnImage( Object element, int columnIndex )
        {
            if ( columnIndex == 0 )
            {
                TracServer server = (TracServer) element;
                return Images.get( server.isConnected() ? Images.ServerConnected
                                                       : Images.ServerDisconnected );
            }
            
            return null;
        }
        
        public String getColumnText( Object element, int columnIndex )
        {
            TracServer server = (TracServer) element;
            switch ( columnIndex ) {
                case 1:
                    return server.getName();
                case 2:
                    return server.getUrl().toString();
                    
                default:
                    return null;
            }
        }
        
        public void addListener( ILabelProviderListener listener )
        {}
        
        public void dispose()
        {}
        
        public boolean isLabelProperty( Object element, String property )
        {
            return false;
        }
        
        public void removeListener( ILabelProviderListener listener )
        {}
        
    }
}
