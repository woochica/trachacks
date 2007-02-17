/**
 * 
 */
package mm.eclipse.trac.decorators;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.viewers.IDecoration;
import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.ILightweightLabelDecorator;

/**
 * @author Matteo Merli
 * 
 */
public class TracDecorator implements ILightweightLabelDecorator
{
    
    public void decorate( Object obj, IDecoration decoration )
    {
        Log.info( "decorate: " + obj );
        if ( obj instanceof WikiPage )
        {
            WikiPage page = (WikiPage) obj;
            decoration.addSuffix( " hola " + page.exists() );
        }
    }
    
    public void dispose()
    {}
    
    public boolean isLabelProperty( Object obj, String property )
    {
        return false;
    }
    
    public void addListener( ILabelProviderListener listener )
    {}
    
    public void removeListener( ILabelProviderListener listener )
    {}
    
}
