/**
 * 
 */
package org.trachacks.wikieditor.service;

import java.util.Date;
import java.util.List;

import org.trachacks.wikieditor.model.PageInfo;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.GatewayTimeoutException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;
import org.trachacks.wikieditor.model.exception.PageVersionNotFoundException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.ProxyAuthenticationRequiredException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;

import com.sun.jmx.remote.internal.ProxyRef;

/**
 * @author ivan
 *
 */
public interface WikiService {

	public boolean testConnection(ServerDetails server) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException ;
	public boolean testConnection(ServerDetails server, ProxySettings proxySettings)	throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException, 
														GatewayTimeoutException, ProxyAuthenticationRequiredException ;
	
	public String[] getPageNames();
	@Deprecated
	public List<PageInfo> loadPages();
	
	public boolean isLocallyEdited(String pageName);
	public PageVersion loadPageVersion(String pageName) throws PageNotFoundException;
	public PageVersion edit(PageVersion pageVersion);
	public PageVersion commit(PageVersion pageVersion) throws ConcurrentEditException, PageNotModifiedException;
	public PageVersion commit(PageVersion pageVersion, boolean isMinorEdit) throws ConcurrentEditException, PageNotModifiedException;
	public PageVersion unedit(PageVersion pageVersion);
	public PageVersion forceCommit(PageVersion pageVersion) throws PageNotModifiedException;
	public PageVersion getLatestVersion(String pageName) throws PageNotFoundException;
	
	public  boolean deletePage(String name) throws PageNotFoundException, PermissionDeniedException;
	public  boolean deletePageVersion(String name, int version) throws PageNotFoundException, PageVersionNotFoundException, PermissionDeniedException;

	
	public List<PageInfo> getRecentChanges(Date since);
	public List<PageInfo> getPageHistory(String pageName) throws PageNotFoundException;
	public PageVersion loadPageVersion(String pageName, int version) throws PageNotFoundException,PageVersionNotFoundException;
	
	public String wikiToHtml(String wikiText);
	
}
