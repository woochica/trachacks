/**
 * 
 */
package mm.eclipse.trac.editors;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.IPersistableElement;
import org.eclipse.ui.IStorageEditorInput;

/**
 * @author Matteo Merli
 * 
 */
public class WikiEditorInput implements IStorageEditorInput
{
    private WikiPage page;
    private IStorage storage;
    
    public WikiEditorInput( WikiPage page )
    {
        this.page = page;
        storage = new WikiEditorStorage( page );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IStorageEditorInput#getStorage()
     */
    public IStorage getStorage() throws CoreException
    {
        return storage;
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IEditorInput#exists()
     */
    public boolean exists()
    {
        return page.exists();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IEditorInput#getImageDescriptor()
     */
    public ImageDescriptor getImageDescriptor()
    {
        return Activator.getImageDescriptor( "icons/trac_16.png" );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IEditorInput#getName()
     */
    public String getName()
    {
        return page.getSimpleName();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IEditorInput#getPersistable()
     */
    public IPersistableElement getPersistable()
    {
        return null;
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IEditorInput#getToolTipText()
     */
    public String getToolTipText()
    {
        return page.getFullName();
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.core.runtime.IAdaptable#getAdapter(java.lang.Class)
     */
    public Object getAdapter( Class adapter )
    {
        if ( WikiPage.class.equals( adapter ) )
            return page;
        
        // Log.info( "WikiEditorInput.getAdapter: " + adapter.toString() );
        /*
        if ( IFile.class.equals( adapter ) )
            return storage;
        if ( IResource.class.equals( adapter ) )
            return storage;
        */
        // Log.info( "Null" );
        return null;
    }
    
    public WikiPage getWikiPage()
    {
        return page;
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see java.lang.Object#equals(java.lang.Object)
     */
    @Override
    public boolean equals( Object obj )
    {
        if ( obj instanceof WikiEditorInput )
        {
            WikiEditorInput other = (WikiEditorInput) obj;
            return this.storage.getName() == other.storage.getName();
        }
        return false;
    }
    
}
