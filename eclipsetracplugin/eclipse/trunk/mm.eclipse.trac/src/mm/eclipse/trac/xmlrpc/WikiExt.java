package mm.eclipse.trac.xmlrpc;

import java.util.Map;

public interface WikiExt
{
    /**
     * Return an array of page versions info
     * 
     * @param pagename
     *            The page name
     * @return
     */
    Object[] getPageVersions( String pagename );
    
    boolean hasChildren( String pagename );
    
    Map<String, Map<String,Object>> getChildren( String pagename );
    
    /**
     * Return the list of registered wiki macros.
     * 
     * @return a map whose keys are the macro names and values are macro
     *         descriptions.
     */
    Map<String, String> getMacros();
    
}
