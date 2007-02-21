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
    private WeakCollection<ITracListener> listeners;
    
    public void addListener( ITracListener listener )
    {
        if ( listeners == null ) listeners = new WeakCollection<ITracListener>();
        
        listeners.add( listener );
    }
    
    public void removeListener( ITracListener listener )
    {
        if ( listeners != null )
        {
            listeners.remove( listener );
        }
    }
    
    protected void notifyChanged()
    {
        if ( listeners == null ) return;
        /*
        Display.getDefault().asyncExec( new Runnable() {
            public void run()
            {
          */      for ( ITracListener listener : listeners )
                    listener.tracResourceModified( this );
          /*  }
        } ); */
    }
    
}
