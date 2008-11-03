package mm.eclipse.trac.editors;

import java.io.InputStream;

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
    
    public String getCharset() throws CoreException
    {
        return Encoding;
    }
    
    public InputStream getContents() throws CoreException
    {
        return page.getContent();
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
    
    @SuppressWarnings("unchecked")
    public Object getAdapter( Class adapter )
    {
        Log.info( "Storage: Requesting adapter for " + adapter );
        return null;
    }
    
}
