package mm.eclipse.trac.views;

import java.util.Collection;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.models.ITracListener;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.models.WikiPage;
import mm.eclipse.trac.views.actions.IActionsProvider;
import mm.eclipse.trac.views.actions.TracServerActionProvider;
import mm.eclipse.trac.views.actions.WikiPageActionsProvider;

import org.eclipse.jface.action.IMenuListener;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.MenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.DecoratingLabelProvider;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.jface.viewers.ViewerSorter;
import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Menu;
import org.eclipse.ui.IActionBars;
import org.eclipse.ui.IDecoratorManager;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.navigator.CommonViewer;
import org.eclipse.ui.part.DrillDownAdapter;
import org.eclipse.ui.part.ViewPart;

public class TracNavigator extends ViewPart implements ITracListener
{
    private CommonViewer     viewer;
    
    private DrillDownAdapter drillDownAdapter;
    
    private IActionsProvider tracServerActions;
    
    private IActionsProvider wikiPageActions;
    
    class NameSorter extends ViewerSorter
    {}
    
    /**
     * The constructor.
     */
    public TracNavigator()
    {}
    
    /**
     * This is a callback that will allow us to create the viewer and initialize
     * it.
     */
    public void createPartControl( Composite parent )
    {
        viewer = new CommonViewer( "mm.eclipse.trac.views", parent, SWT.MULTI
                                                                    | SWT.H_SCROLL
                                                                    | SWT.V_SCROLL );
        drillDownAdapter = new DrillDownAdapter( viewer );
        viewer.setContentProvider( new WikiContentProvider() );
        
        TracLabelProvider labelProvider = new TracLabelProvider();
        IDecoratorManager manager = Activator.getDefault().getWorkbench()
                .getDecoratorManager();
        viewer.setLabelProvider( new DecoratingLabelProvider( labelProvider, manager ) );
        
        viewer.setSorter( new NameSorter() );
        viewer.setInput( TracServerList.getInstance() );
        TracServerList.getInstance().addListener( this );
        
        makeActions();
        hookContextMenu();
        contributeToActionBars();
    }
    
    private void hookContextMenu()
    {
        MenuManager menuMgr = new MenuManager( "#PopupMenu" );
        menuMgr.setRemoveAllWhenShown( true );
        menuMgr.addMenuListener( new IMenuListener() {
            public void menuAboutToShow( IMenuManager manager )
            {
                IStructuredSelection selection = (IStructuredSelection) viewer
                        .getSelection();
                
                tracServerActions.fillMenu( manager, selection );
                manager.add(  new Separator() );
                wikiPageActions.fillMenu( manager, selection );
                manager.add(  new Separator() );
                drillDownAdapter.addNavigationActions( manager );
                // Other plug-ins can contribute there actions here
                manager.add( new Separator( IWorkbenchActionConstants.MB_ADDITIONS ) );
            }
        } );
        Menu menu = menuMgr.createContextMenu( viewer.getControl() );
        viewer.getControl().setMenu( menu );
        getSite().registerContextMenu( menuMgr, viewer );
    }
    
    private void contributeToActionBars()
    {
        IActionBars bars = getViewSite().getActionBars();
        fillLocalPullDown( bars.getMenuManager() );
        fillLocalToolBar( bars.getToolBarManager() );
    }
    
    private void fillLocalPullDown( IMenuManager manager )
    {
        manager.add( new Separator() );
    }
    
    private void fillLocalToolBar( IToolBarManager manager )
    {
        manager.add( new Separator() );
        drillDownAdapter.addNavigationActions( manager );
    }
    
    private void makeActions()
    {
        tracServerActions = new TracServerActionProvider( viewer );
        wikiPageActions = new WikiPageActionsProvider( viewer );
    }
    
    /**
     * Passing the focus request to the viewer's control.
     */
    public void setFocus()
    {
        viewer.getControl().setFocus();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.models.ITracListener#wikiPageChanged(java.lang.Object)
     */
    public void tracResourceModified( Object element )
    {
        viewer.refresh( element, true );
    }
    
    // ////////////////////////////////////////////////////////////////////////
    
    private class WikiContentProvider implements IStructuredContentProvider,
            ITreeContentProvider
    {
        
        public Object[] getElements( Object parent )
        {
            return getChildren( parent );
        }
        
        public void dispose()
        {}
        
        public void inputChanged( Viewer arg0, Object arg1, Object arg2 )
        {}
        
        public Object[] getChildren( Object obj )
        {
            if ( obj instanceof TracServerList )
            {
                TracServerList serverList = (TracServerList) obj;
                for ( TracServer s : serverList )
                    s.addListener( TracNavigator.this );
                return serverList.getServers().toArray();
            }
            if ( obj instanceof TracServer )
            {
                TracServer server = (TracServer) obj;
                
                if ( server.isConnected() )
                {
                    WikiPage rootPage = new WikiPage( server, "", true );
                    rootPage.setRoot( true );
                    return new WikiPage[] { rootPage };
                }
                else
                {
                    return new WikiPage[0];
                }
            }
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                Collection<WikiPage> children = page.getChildren();
                for ( WikiPage p : children )
                    p.addListener( TracNavigator.this );
                return children.toArray();
            }
            
            return null;
        }
        
        public Object getParent( Object obj )
        {
            if ( obj instanceof TracServer ) { return TracServerList.getInstance(); }
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                if ( page.isRoot() )
                    return page.getServer();
                else return page.getParent();
            }
            return null;
        }
        
        public boolean hasChildren( Object obj )
        {
            if ( obj instanceof TracServer )
            {
                TracServer server = (TracServer) obj;
                return server.isConnected();
            }
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                return page.hasChildren();
            }
            return false;
        }
        
    }
}
