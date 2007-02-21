/**
 * 
 */
package mm.eclipse.trac.views;

import mm.eclipse.trac.Images;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.swt.graphics.Image;
import org.eclipse.ui.ISharedImages;
import org.eclipse.ui.PlatformUI;

/**
 * @author Matteo Merli
 * 
 */
public class TracLabelProvider extends LabelProvider
{
    
    @Override
    public String getText( Object obj )
    {
        if ( obj instanceof TracServerList )
        {
            return "Server List";
        }
        else if ( obj instanceof TracServer )
        {
            TracServer server = (TracServer) obj;
            return server.getName();
        }
        else if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            if ( page.isRoot() )
                return "Trac Wiki";
            else return page.getSimpleName();
        }
        else return "Not identified object";
    }
    
    @Override
    public Image getImage( Object obj )
    {
        if ( obj instanceof TracServer )
        {
            TracServer server = (TracServer) obj;
            return Images.get( server.isConnected() ? Images.ServerConnected
                                                    : Images.ServerDisconnected );
        }
        else if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            
            if ( page.exists() )
                return Images.get( Images.Trac16 );
            else return getSharedImage( ISharedImages.IMG_OBJ_FOLDER );
        }
        
        return getSharedImage( ISharedImages.IMG_OBJ_ELEMENT );
    }
    
    private Image getSharedImage( String imageKey )
    {
        return PlatformUI.getWorkbench().getSharedImages().getImage( imageKey );
    }
    
}
