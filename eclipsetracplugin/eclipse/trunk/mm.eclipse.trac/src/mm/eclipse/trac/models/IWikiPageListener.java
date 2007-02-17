/**
 * 
 */
package mm.eclipse.trac.models;

/**
 * @author Matteo Merli
 * 
 */
public interface IWikiPageListener
{
    /**
     * Notify when the observed page gets modified.
     * 
     * @param page
     *            The modified wiki page.
     */
    void wikiPageChanged( Object page );
    
}
