package mm.eclipse.trac.editors;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.StringReader;
import java.io.Writer;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;

public class WikiEditorStorage implements IStorage
{
    private static final String Encoding = "utf-8";
    
    private WikiPage page;
    
    public WikiEditorStorage( WikiPage page )
    {
        this.page = page;
    }
    
    private class StreamAdapter extends InputStream
    {
        private ByteArrayInputStream istream;
        
        public StreamAdapter( Reader reader )
        {
            ByteArrayOutputStream ostream = new ByteArrayOutputStream();
            try
            {
                Writer writer = new OutputStreamWriter( ostream, Encoding );
                while ( true )
                {
                    int c = reader.read();
                    if ( c == -1 )
                        break;
                    writer.write( c );
                }
                
                writer.close();
            } catch ( Exception e )
            {
                Log.error( "Conversion error.", e );
            }
            
            Log.info( "Size: " + ostream.size() );
            
            istream = new ByteArrayInputStream( ostream.toByteArray() );
        }
        
        @Override
        public int read() throws IOException
        {
            return istream.read();
        }
    }
    
    public String getCharset() throws CoreException
    {
        return Encoding;
    }
    
    public InputStream getContents() throws CoreException
    {
        StringReader reader = new StringReader( page.getContent() );
        return new StreamAdapter( reader );
    }
    
    public IPath getFullPath()
    {
        Log.info( "IFile.getFullPath" );
        return null;
    }
    
    public String getName()
    {
        return page.getFullName();
    }
    
    public boolean isReadOnly()
    {
        return false;
    }
    
    public Object getAdapter( Class adapter )
    {
        Log.info( "Storage: Requesting adapter for " + adapter );
        return null;
    }
    
}
