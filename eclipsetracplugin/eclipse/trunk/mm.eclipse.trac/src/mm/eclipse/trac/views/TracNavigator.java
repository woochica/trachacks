package mm.eclipse.trac.views;

import java.util.Collection;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.IWikiPageListener;
import mm.eclipse.trac.models.WikiPage;
import mm.eclipse.trac.views.actions.CommitPage;
import mm.eclipse.trac.views.actions.OpenEditor;
import mm.eclipse.trac.xmlrpc.Trac;

import org.eclipse.core.runtime.Preferences.IPropertyChangeListener;
import org.eclipse.core.runtime.Preferences.PropertyChangeEvent;
import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuListener;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.MenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.DecoratingLabelProvider;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.jface.viewers.ViewerSorter;
import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Menu;
import org.eclipse.ui.IActionBars;
import org.eclipse.ui.IDecoratorManager;
import org.eclipse.ui.ISharedImages;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.navigator.CommonViewer;
import org.eclipse.ui.part.DrillDownAdapter;
import org.eclipse.ui.part.ViewPart;

public class TracNavigator extends ViewPart implements IPropertyChangeListener,
        IWikiPageListener
{
    private CommonViewer     viewer;
    
    private DrillDownAdapter drillDownAdapter;
    
    private Action           action1;
    
    private Action           actionCommitPage;
    
    private Action           actionOpenEditor;
    
    class NameSorter extends ViewerSorter
    {
    }
    
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
                | SWT.H_SCROLL | SWT.V_SCROLL );
        drillDownAdapter = new DrillDownAdapter( viewer );
        viewer.setContentProvider( new WikiContentProvider() );
        
        TracLabelProvider labelProvider = new TracLabelProvider();
        IDecoratorManager manager = Activator.getDefault().getWorkbench()
                .getDecoratorManager();
        viewer.setLabelProvider( new DecoratingLabelProvider( labelProvider, manager ) );
        
        viewer.setSorter( new NameSorter() );
        propertyChange( null );
        
        makeActions();
        hookContextMenu();
        contributeToActionBars();
        
        Activator.getDefault().getPluginPreferences().addPropertyChangeListener( this );
    }
    
    public void propertyChange( PropertyChangeEvent event )
    {
        Log.info( "TracNavigator: Configuration changed. Reload Tree" );
        if ( !Trac.getInstance().isEnabled() )
        {
            viewer.setInput( null );
            return;
        }
        
        WikiPage invisibleRoot = new WikiPage( "", false );
        WikiPage root = new WikiPage( "", false );
        root.setRoot( true );
        invisibleRoot.addChild( root );
        viewer.setInput( invisibleRoot );
    }
    
    private void hookContextMenu()
    {
        MenuManager menuMgr = new MenuManager( "#PopupMenu" );
        menuMgr.setRemoveAllWhenShown( true );
        menuMgr.addMenuListener( new IMenuListener() {
            public void menuAboutToShow( IMenuManager manager )
            {
                TracNavigator.this.fillContextMenu( manager );
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
        manager.add( actionOpenEditor );
        manager.add( actionCommitPage );
        manager.add( new Separator() );
        manager.add( action1 );
    }
    
    private void fillContextMenu( IMenuManager manager )
    {
        manager.add( actionOpenEditor );
        manager.add( actionCommitPage );
        manager.add( new Separator() );
        manager.add( action1 );
        
        drillDownAdapter.addNavigationActions( manager );
        // Other plug-ins can contribute there actions here
        manager.add( new Separator( IWorkbenchActionConstants.MB_ADDITIONS ) );
    }
    
    private void fillLocalToolBar( IToolBarManager manager )
    {
        manager.add( action1 );
        manager.add( new Separator() );
        drillDownAdapter.addNavigationActions( manager );
    }
    
    private void makeActions()
    {
        actionOpenEditor = new OpenEditor( viewer );
        
        action1 = new Action() {
            public void run()
            {
                showMessage( "Action 1 executed" );
            }
        };
        action1.setText( "Action 1" );
        action1.setToolTipText( "Action 1 tooltip" );
        action1.setImageDescriptor( PlatformUI.getWorkbench().getSharedImages()
                .getImageDescriptor( ISharedImages.IMG_OBJS_INFO_TSK ) );
        
        actionCommitPage = new CommitPage( viewer );
    }
    
    private void showMessage( String message )
    {
        MessageDialog.openInformation( viewer.getControl().getShell(), "Sample View",
                                       message );
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
     * @see mm.eclipse.trac.models.IWikiPageListener#wikiPageChanged(java.lang.Object)
     */
    public void wikiPageChanged( Object page )
    {
        viewer.refresh( page, true );
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
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                return page.getParent();
            }
            return null;
        }
        
        public boolean hasChildren( Object obj )
        {
            if ( obj instanceof WikiPage )
            {
                WikiPage page = (WikiPage) obj;
                return page.hasChildren();
            }
            return false;
        }
        
    }
}
