package mm.eclipse.trac.views;

import java.text.SimpleDateFormat;
import java.util.List;

import mm.eclipse.trac.editors.WikiEditor;
import mm.eclipse.trac.editors.WikiEditorInput;
import mm.eclipse.trac.models.IWikiPageListener;
import mm.eclipse.trac.models.WikiPage;
import mm.eclipse.trac.models.WikiPageVersion;

import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.ITableLabelProvider;
import org.eclipse.jface.viewers.TableViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Table;
import org.eclipse.swt.widgets.TableColumn;
import org.eclipse.ui.IPartListener;
import org.eclipse.ui.IViewSite;
import org.eclipse.ui.IWorkbenchPart;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.part.ViewPart;

public class WikiPageHistory extends ViewPart implements IPartListener, IWikiPageListener
{
    private TableViewer viewer;
    
    private WikiPage    page;
    
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
        column.setText( "Version" );
        column.setWidth( 100 );
        
        column = new TableColumn( table, SWT.LEFT, 1 );
        column.setText( "Date" );
        column.setWidth( 300 );
        
        column = new TableColumn( table, SWT.LEFT, 2 );
        column.setText( "Author" );
        column.setWidth( 200 );
        
        column = new TableColumn( table, SWT.LEFT, 3 );
        column.setText( "Comment" );
        column.setWidth( 300 );
        
        viewer = new TableViewer( table );
        viewer.setContentProvider( new HistoryContentProvider() );
        viewer.setLabelProvider( new HistoryLabelProvider() );
    }
    
    @Override
    public void init( IViewSite site ) throws PartInitException
    {
        super.init( site );
        site.getPage().addPartListener( this );
    }
    
    @Override
    public void setFocus()
    {
        viewer.getControl().setFocus();
    }
    
    public void partActivated( IWorkbenchPart part )
    {
        if ( !(part instanceof WikiEditor) ) return;
        
        WikiEditor wikiEditor = (WikiEditor) part;
        
        page = ((WikiEditorInput) wikiEditor.getEditorInput()).getWikiPage();
        page.addListener( this );
        viewer.setInput( page.getVersions() );
        setContentDescription( "Page description for " + page.getFullName() );
    }
    
    public void partBroughtToTop( IWorkbenchPart part )
    {}
    
    public void partClosed( IWorkbenchPart part )
    {
        if ( !(part instanceof WikiEditor) ) return;
        viewer.setInput( null );
        
        if ( page != null )
        {
            page.removeListener( this );
            page = null;
        }
    }
    
    public void partDeactivated( IWorkbenchPart part )
    {}
    
    public void partOpened( IWorkbenchPart part )
    {
    // 
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see mm.eclipse.trac.models.IWikiPageListener#wikiPageChanged(java.lang.Object)
     */
    public void wikiPageChanged( Object page )
    {
        if ( page == this.page && viewer.getInput() != null )
        {
            viewer.setInput( ((WikiPage) page).getVersions() );
        }
    }
    
    private static class HistoryContentProvider implements IStructuredContentProvider
    {
        private static final Object[] emptySet = new Object[0];
        
        public Object[] getElements( Object inputElement )
        {
            if ( inputElement == null ) return emptySet;
            
            return ((List) inputElement).toArray();
        }
        
        public void dispose()
        {}
        
        public void inputChanged( Viewer viewer, Object oldInput, Object newInput )
        {}
        
    }
    
    private static class HistoryLabelProvider implements ITableLabelProvider
    {
        
        public Image getColumnImage( Object element, int columnIndex )
        {
            return null;
        }
        
        public String getColumnText( Object element, int columnIndex )
        {
            WikiPageVersion version = (WikiPageVersion) element;
            switch ( columnIndex ) {
                case 0:
                    return String.valueOf( version.getVersion() );
                case 1:
                    return (new SimpleDateFormat( "yyyy-MM-dd HH:mm" )).format( version
                            .getDate() );
                case 2:
                    return version.getAuthor();
                case 3:
                    return version.getComment();
                    
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
