package mm.eclipse.trac.xmlrpc;

import java.util.Map;

public interface Wiki
{
    /**
     * @return 2 with this version of the Trac API.
     */
    int getRPCVersionSupported();
    
    /**
     * Get the raw Wiki text of page, latest version.
     * 
     * @param pagename
     * @return
     */
    String getPage( String pagename );
    
    /**
     * Get the raw Wiki text of page, specify version.
     * 
     * @param pagename
     * @param version
     * @return
     */
    String getPageVersion( String pagename, int version );
    
    /**
     * Get the HTML rendering of page, latest version.
     * 
     * @param pagename
     * @return
     */
    String getPageHTML( String pagename );
    
    /**
     * Get the HTML rendering of page, specify version.
     * 
     * @param pagename
     * @param version
     * @return
     */
    String getPageHTMLVersion( String pagename, int version );
    
    /**
     * @return a list of all pages. The result is an array of utf8 pagenames.
     */
    Object[] getAllPages();
    
    /**
     * Writes the content of the page.
     * 
     * @param name The page name
     * @param content The page wiki content
     * @param attributes A map containing t
     * @return
     */
    boolean putPage( String name, String content, Map<String, String> attributes );
    
    /**
     * Render arbitrary Wiki text as HTML.
     * 
     * @param text
     * @return
     */
    String wikiToHtml( String text );
}
