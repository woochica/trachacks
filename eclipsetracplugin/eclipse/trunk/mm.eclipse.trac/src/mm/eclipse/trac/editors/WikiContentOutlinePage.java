package mm.eclipse.trac.editors;

import java.text.MessageFormat;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.editors.model.WikiSection;
import mm.eclipse.trac.editors.model.WikiTextParser;

import org.eclipse.jface.text.BadPositionCategoryException;
import org.eclipse.jface.text.DefaultPositionUpdater;
import org.eclipse.jface.text.DocumentEvent;
import org.eclipse.jface.text.DocumentPartitioningChangedEvent;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentPartitioningListener;
import org.eclipse.jface.text.IDocumentPartitioningListenerExtension2;
import org.eclipse.jface.text.IPositionUpdater;
import org.eclipse.jface.text.ITypedRegion;
import org.eclipse.jface.text.Position;
import org.eclipse.jface.viewers.AbstractTreeViewer;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.texteditor.IDocumentProvider;
import org.eclipse.ui.views.contentoutline.ContentOutlinePage;

public class WikiContentOutlinePage extends ContentOutlinePage implements
        IDocumentPartitioningListener, IDocumentPartitioningListenerExtension2,
        IPositionUpdater
{
    private IDocumentProvider provider;
    
    private WikiSourceEditor  editor;
    
    private IPositionUpdater  positionsUpdater;
    
    public WikiContentOutlinePage( IDocumentProvider provider, WikiSourceEditor editor )
    {
        this.provider = provider;
        this.editor = editor;
    }
    
    public void createControl( Composite parent )
    {
        super.createControl( parent );
        TreeViewer tree = getTreeViewer();
        tree.setLabelProvider( new OutlineLabelProvider() );
        tree.setContentProvider( new OutlineContentProvider() );
        tree.setAutoExpandLevel( AbstractTreeViewer.ALL_LEVELS );
        tree.addSelectionChangedListener( this );
        
        IDocument document = editor.getDocument();
        
        positionsUpdater = new DefaultPositionUpdater( WikiTextParser.PositionCategory );
        document.addPositionUpdater( positionsUpdater );
        // document.addPositionUpdater( this );
        
        document.addDocumentPartitioningListener( this );
        
        WikiTextParser parser = new WikiTextParser( document );
        WikiSection section = parser.parse();
        getTreeViewer().setInput( section );
    }
    
    public void selectionChanged( SelectionChangedEvent event )
    {
        if ( event.getSelection() instanceof IStructuredSelection )
        {
            IStructuredSelection selection = (IStructuredSelection) event.getSelection();
            Object obj = selection.getFirstElement();
            if ( obj instanceof WikiSection )
            {
                WikiSection section = (WikiSection) obj;
                String s = MessageFormat
                        .format( "editor.selectAndReveal( {0}, {1} );", section
                                .getOffset(), section.getLength() );
                Log.info( s );
                
                editor.selectAndReveal( section.getOffset(), section.getLength() );
            }
        }
    }
    
    public void setWiki( WikiSection section )
    {
        getTreeViewer().setInput( section );
    }
    
    public void dispose()
    {
        super.dispose();
        editor.outlinePageClosed();
        editor = null;
    }
    
    public void documentPartitioningChanged( DocumentPartitioningChangedEvent event )
    {
        WikiTextParser parser = new WikiTextParser( event.getDocument() );
        WikiSection section = parser.parse();
        getTreeViewer().setInput( section );
    }
    
    public void documentPartitioningChanged( IDocument document )
    {
        Log.info( "Has changed!" );
        /*
         * try { Position[] newpositions = document .getPositions(
         * WikiPartitionScanner.SectionToken );
         * 
         * if ( positions != null ) {
         */
        // document partitioning changed, wholesale replace
        /*
         * }
         * 
         * positions = newpositions; } catch ( BadPositionCategoryException e ) {
         * Log.error( "Unexpected error in RawPartitonModel::updatePositions", e );
         * positions = new Position[0]; }
         */
    }
    
    /**
     * The manipulation described by the document event will be performed.
     * 
     * @param event
     *            the document event describing the document change
     */
    public void documentAboutToBeChanged( DocumentEvent event )
    {}
    
    /**
     * The manipulation described by the document event has been performed.
     * 
     * @param event
     *            the document event describing the document change
     */
    public void documentChanged( DocumentEvent event )
    {
        try
        {
            for ( Position p : event.getDocument()
                    .getPositions( WikiTextParser.PositionCategory ) )
            {
                Log.info( "Position: " + p.offset + ", " + p.length );
            }
        } catch ( BadPositionCategoryException e )
        {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
    
    public void update( DocumentEvent event )
    {
        Log.info( "Changed position:" + event.getOffset() );
        
        IDocument doc = editor.getDocument();
        try
        {
            for ( Position p : doc.getPositions( WikiTextParser.PositionCategory ) )
            {
                p.offset += 5;
                Log.info( "Update Position: " + p.offset + ", " + p.length );
            }
        } catch ( BadPositionCategoryException e )
        {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        
        WikiSection rootSection = (WikiSection) getTreeViewer().getInput();
        
        ITypedRegion region = doc.getDocumentPartitioner()
                .getPartition( event.getOffset() );
        // Log.info( "Found region: " + region.getType() + " - " +
        // region.getOffset() );
        
        // WikiSection current = rootSection.find( event.getOffset(), -1, null
        // );
        // if ( current != null )
        // {
        // Log.info( "We are in section: " + current.getName() );
        // }
    }
    
    // ////////////////////////////////////////////////////////////
    
    private static class OutlineContentProvider implements ITreeContentProvider,
            IStructuredContentProvider
    {
        
        public Object[] getChildren( Object parentElement )
        {
            return ((WikiSection) parentElement).getChildren().toArray();
        }
        
        public Object getParent( Object element )
        {
            return ((WikiSection) element).getParent();
        }
        
        public boolean hasChildren( Object element )
        {
            Object[] children = getChildren( element );
            return children != null && children.length != 0;
        }
        
        public Object[] getElements( Object inputElement )
        {
            return getChildren( inputElement );
        }
        
        public void dispose()
        {
        // do nothing
        }
        
        public void inputChanged( Viewer viewer, Object oldInput, Object newInput )
        {}
    }
    
    private static class OutlineLabelProvider extends LabelProvider
    {
        
        private static final Image stepIcon = createImage( "step.gif" );
        
        public static Image createImage( String icon )
        {
            return Activator.getImageDescriptor( "icons/" + icon ).createImage();
        }
        
        public String getText( Object element )
        {
            return ((WikiSection) element).getName();
        }
        
        public Image getImage( Object element )
        {
            if ( element instanceof WikiSection ) return stepIcon;
            return super.getImage( element );
        }
    }
}
