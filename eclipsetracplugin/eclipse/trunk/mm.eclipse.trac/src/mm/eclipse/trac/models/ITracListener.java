/**
 * 
 */
package mm.eclipse.trac.models;

/**
 * @author Matteo Merli
 * 
 */
public interface ITracListener
{
    /**
     * Notify when the observed page gets modified.
     * 
     * @param resource
     *            The modified wiki page.
     */
    void tracResourceModified( Object resource );
    
}
