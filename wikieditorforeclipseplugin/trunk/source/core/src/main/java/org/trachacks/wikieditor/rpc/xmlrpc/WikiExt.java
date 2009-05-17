/**
 * 
 */
package org.trachacks.wikieditor.rpc.xmlrpc;

/**
 * @author ivan
 *
 */
public interface WikiExt {

    /**
     * Return an array of page versions info
     * 
     * @param pagename
     *            The page name
     * @return
     */
    Object[] getPageVersions( String pagename );
    
}
