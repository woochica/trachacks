package org.trachacks.wikieditor.eclipse.plugin.editor.model;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.BadPositionCategoryException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentPartitioner;
import org.eclipse.jface.text.ITypedRegion;
import org.eclipse.jface.text.Position;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiPartitionScanner;

public class WikiTextParser
{
    
    public static final String PositionCategory = "SectionPositonCategory";
    
    private IDocument          document;
    
    public WikiTextParser( IDocument document )
    {
        this.document = document;
    }
    
    public WikiSection parse()
    {
        int length = document.getLength();
        
        IDocumentPartitioner partitioner = document.getDocumentPartitioner();
        ITypedRegion[] regions;
        regions = partitioner.computePartitioning( 0, length );
        
        try
        {
            document.removePositionCategory( PositionCategory );
        } catch ( BadPositionCategoryException e )
        {
        }
        
        document.addPositionCategory( PositionCategory );
        
        WikiSection rootSection = new WikiSection( null, -1, null );
        WikiSection current = rootSection;
        
        for ( ITypedRegion region : regions )
        {
            String type = region.getType();
            
            if ( type != WikiPartitionScanner.SectionToken ) continue;
            
            String name = "";
            try
            {
                name = document.get( region.getOffset(), region.getLength() );
            } catch ( BadLocationException e )
            {
            }
            
            int level = name.lastIndexOf( '=' ) + 1;
            name = name.replace( "=", "" ).trim();
            
            Position position = new Position( region.getOffset(), region.getLength() );
            try
            {
                document.addPosition( PositionCategory, position );
            } catch ( BadLocationException e )
            {
            } catch ( BadPositionCategoryException e )
            {
            }
            WikiSection section = new WikiSection( name, level, position );
            
            // We must climb up the three to find the father
            while ( level <= current.getHeaderLevel() )
            {
                current = current.getParent();
            }
            
            current.add( section );
            section.setParent( current );
            current = section;
        }
        
        return rootSection;
    }
    
}
