/**
 * 
 */
package org.trachacks.wikieditor.rpc.xmlrpc;

import java.util.Date;
import java.util.Map;

/**
 *
 *
 */
public interface Wiki {
	
	public static final int RPC_API_VERSION = 2;
	
	/**
	 * @return 2 with this version of the Trac API.
	 */
	public int getRPCVersionSupported();
	
	/**
	 * 
	 * @param since
	 * @return Returns an array of Map<String, Object> pageInfo
	 */
	public Object[] getRecentChanges(Date since);

	/**
	 * Get the raw Wiki text of page, latest version.
	 * 
	 * @param pagename
	 * @return
	 */
	public String getPage(String pagename);

	/**
	 * Get the raw Wiki text of page, specify version.
	 * 
	 * @param pagename
	 * @param version
	 * @return
	 */
	public String getPageVersion(String pagename, int version);
	
	/**
	 * @return a list of all pages. The result is an array of utf8 pagenames.
	 */
	public Object[] getAllPages();
	
	/**
	 *  returns a Map&lt;String, Object> with elements:
	 * <ul>
	 *  <li>name (String): the canonical page name.</li>
	 *  <li>lastModified (Date): Last modification date, UTC.</li>
	 *  <li>author (String): author name.</li>
	 *  <li>version (int): current version</li>
	 * </ul>
	 */
	public Map<String, Object> getPageInfo(String pagename);
    
	/**
	 *  returns a Map&lt;String, Object> with elements for given version:
	 * <ul>
	 *  <li>name (String): the canonical page name.</li>
	 *  <li>lastModified (Date): Last modification date, UTC.</li>
	 *  <li>author (String): author name.</li>
	 *  <li>version (int): current version</li>
	 * </ul>
	 */
	public Map<String, Object> getPageInfoVersion(String pagename, int version); 

	/**
	 * Writes the content of the page.
	 * 
	 * @param name
	 *            The page name
	 * @param content
	 *            The page wiki content
	 * @param attributes
	 *            A map containing t
	 * @return
	 */
	public boolean putPage(String name, String content, Map<String, String> attributes);

	/**
	 * Delete a Wiki page (all versions). 
	 * Attachments will also be deleted if page no longer exists.  Requires WIKI_DELETE
	 * 
	 * @param name
	 * @return Returns True for success.
	 */
	public  boolean deletePage(String name);
	
	/**
	 * Delete a specific version of the Wiki page. 
	 * Attachments will also be deleted if page no longer exists.  Requires WIKI_DELETE
	 * 
	 * @param name
	 * @param version
	 * @return Returns True for success.
	 */	
	public  boolean deletePage(String name, int version);
	
	/**
	 * Render arbitrary Wiki text as HTML.
	 * 
	 * @param text
	 * @return
	 */
	public String wikiToHtml(String text);
}
