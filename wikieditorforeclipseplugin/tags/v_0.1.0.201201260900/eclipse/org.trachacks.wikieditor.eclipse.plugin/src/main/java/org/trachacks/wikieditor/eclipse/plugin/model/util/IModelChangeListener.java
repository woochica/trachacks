/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model.util;

/**
 * @author Matteo Merli
 * 
 */
public interface IModelChangeListener
{
    /**
     * Notify when the observed page gets modified.
     * 
     * @param resource
     *            The modified wiki page.
     */
    void tracResourceModified( Object resource );
    
}
