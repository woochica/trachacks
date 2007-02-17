/**
 * 
 */
package mm.eclipse.trac.models;

import mm.eclipse.trac.util.WeakCollection;

/**
 * @author Matteo Merli
 * 
 */
public abstract class ModelBase
{
    private WeakCollection<IWikiPageListener> listeners;
    
    public void addListener( IWikiPageListener listener )
    {
        if ( listeners == null )
            listeners = new WeakCollection<IWikiPageListener>();
        
        listeners.add( listener );
    }
    
    public void removeListener( IWikiPageListener listener )
    {
        if ( listeners != null )
        {
            listeners.remove( listener );
        }
    }
    
    protected void notifyChanged()
    {
        for ( IWikiPageListener listener : listeners )
            listener.wikiPageChanged( this );
    }
    
}
