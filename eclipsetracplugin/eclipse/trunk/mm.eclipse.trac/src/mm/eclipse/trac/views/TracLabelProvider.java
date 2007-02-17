/**
 * 
 */
package mm.eclipse.trac.views;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.swt.graphics.Image;
import org.eclipse.ui.ISharedImages;
import org.eclipse.ui.PlatformUI;

/**
 * @author mat
 * 
 */
public class TracLabelProvider extends LabelProvider 
{
    
    public String getText( Object obj )
    {
        if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            if ( page.isRoot() )
                return "Trac Wiki";
            else return page.getSimpleName();
        }
        else return "Not identified object";
    }
    
    public Image getImage( Object obj )
    {
        if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            
            if ( page.exists() )
                return getImage( "trac_16.png" );
            else return getSharedImage( ISharedImages.IMG_OBJ_FOLDER );
        }
        
        return getSharedImage( ISharedImages.IMG_OBJ_ELEMENT );
    }
    
    private Image getImage( String fileName )
    {
        return Activator.getImageDescriptor( "icons/" + fileName )
                .createImage();
    }
    
    private Image getSharedImage( String imageKey )
    {
        return PlatformUI.getWorkbench().getSharedImages().getImage( imageKey );
    }
   
}
