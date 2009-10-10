/**
 * 
 */
package org.trachacks.wikieditor.rpc;


import java.util.Date;
import java.util.List;

import org.trachacks.wikieditor.model.PageInfo;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;
import org.trachacks.wikieditor.model.exception.PageVersionNotFoundException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;

/**
 * @author ivan
 *
 */
public interface WikiClient {

	/**
	 * 
	 * @param server
	 * 
	 * @return Returns true if a compatible XML-RPC interface is found, false otherwise.
	 * 
	 * @throws UnknownServerException
	 * @throws ConnectionRefusedException
	 * @throws BadCredentialsException
	 * @throws PermissionDeniedException
	 */
	public boolean testConnection(ServerDetails server, ProxySettings proxySettings) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException;
	
	public String[] getPageNames();
	
	public PageVersion getPageVersion(String pageName) throws PageNotFoundException;
	public PageVersion getPageVersion(String pageName, int version) throws PageNotFoundException, PageVersionNotFoundException;
	public PageVersion savePageVersion(String name, String content, String comment, int baseVersion, boolean isMinorEdit) throws ConcurrentEditException, PageNotModifiedException;
	public PageVersion savePageVersion(String name, String content, String comment) throws PageNotModifiedException;
	
	public  boolean deletePage(String name) throws PageNotFoundException, PermissionDeniedException;
	public  boolean deletePageVersion(String name, int version) throws PageNotFoundException, PageVersionNotFoundException, PermissionDeniedException;

	public List<PageInfo> getRecentChanges(Date since);
	public List<PageInfo> getPageHistory(String pageName) throws PageNotFoundException;
	
	public String wikiToHtml(String wikiText);
}
