/**
 * 
 */
package org.trachacks.wikieditor.rpc;

import java.lang.reflect.UndeclaredThrowableException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
import org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC;
import org.trachacks.wikieditor.rpc.xmlrpc.WikiRPCClientFactory;

/**
 * @author ivan
 *
 */
public class WikiClientImpl implements WikiClient {
	
	private WikiRPC client;

	protected WikiRPC getClient() {
		return client;
	}

	/**
	 * @param client
	 */
	public WikiClientImpl(ServerDetails server) {
		super();
		this.client = WikiRPCClientFactory.getWikiRPCClientInstance(server, null);
	}
	
	/**
	 * 
	 * @param server
	 * @param proxySettings
	 */
	public WikiClientImpl(ServerDetails server, ProxySettings proxySettings) {
		super();
		this.client = WikiRPCClientFactory.getWikiRPCClientInstance(server, proxySettings);
	}

	/**
	 * 
	 */
	public boolean testConnection(ServerDetails server, ProxySettings proxySettings) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		return WikiRPCClientFactory.testConnection(server, proxySettings);
	}
	
	/**
	 * 
	 */
	public String[] getPageNames() {
//		Object[] returnedPages = getClient().getAllPages();
//		Set<String> pages = new HashSet<String>();
//		for (int i = 0; i < returnedPages.length; i++) {
//			String pageName = (String) returnedPages[i];
//			pages.add(pageName);
//		}
//		return pages;
		Object[] returnedPages = getClient().getAllPages();
		String[] pageNames = new String[returnedPages.length];
		for (int i = 0; i < returnedPages.length; i++) {
			pageNames[i] = (String) returnedPages[i];
		}
		return pageNames;
	}


	/**
	 * 
	 */
	public PageVersion getPageVersion(String pageName) throws PageNotFoundException {
		Map<String, Object> pageInfo = getPageInfo(pageName);
		String content = null;
		try {
			content = getClient().getPage(pageName);
		} catch (RuntimeException e) {
			e.printStackTrace();
			throw e;
		}

		//FIXME comment property is missing
		return pageInfo2PageVersion(pageInfo, content);
	}
	
	/**
	 * 
	 */
	public PageVersion getPageVersion(String pageName, int version) throws PageNotFoundException, PageVersionNotFoundException {
		Map<String, Object> pageInfo = getClient().getPageInfoVersion(pageName, version);
		String content = getClient().getPageVersion(pageName, version);

		//FIXME comment property is missing
		return pageInfo2PageVersion(pageInfo, content);
	}
	
	/**
	 * 
	 */
	public PageVersion savePageVersion(String name, String content, String comment, int baseVersion, boolean isMinorEdit) throws ConcurrentEditException, PageNotModifiedException {
		
		
		
		Map<String, String> properties = new HashMap<String, String>();
		properties.put("comment", comment);
		properties.put("version", Integer.toString(baseVersion));
		properties.put("minoredit", Boolean.toString(isMinorEdit));
		
		// FIXME implement Concurrency Control in the server where it belongs
		try {
			Map<String, Object> latestPageInfo = getPageInfo(name);
			int latestVersion = (Integer) latestPageInfo.get("version");
			if(baseVersion != latestVersion) {
				throw new ConcurrentEditException();
			}
		} catch (PageNotFoundException ignore) {
		}
		
		wikiClientPutPage(name, content, properties);
		
		return getPageVersion(name);
	}
	
	/**
	 * 
	 */
	public PageVersion savePageVersion(String name, String content, String comment) throws PageNotModifiedException{
		Map<String, String> properties = new HashMap<String, String>();
		properties.put("comment", comment);
		
		wikiClientPutPage(name, content, properties);
		
		return getPageVersion(name);
	}

	/**
	 * TODO manage WIKI_DELETE PermissionDenied + any other error conditions
	 * @see org.trachacks.wikieditor.rpc.WikiClient#deletePage(java.lang.String)
	 */
	public  boolean deletePage(String name)  throws PageNotFoundException,  PermissionDeniedException{
		try {
			return getClient().deletePage(name);
		} catch (UndeclaredThrowableException e) {
			String message = e.getUndeclaredThrowable().getMessage();
			if(message != null && message.contains("WIKI_DELETE")) {
				throw new PermissionDeniedException();
			}
			throw e;
		}
	}
	/**
	 * TODO manage WIKI_DELETE PermissionDenied + any other error conditions
	 * @see org.trachacks.wikieditor.rpc.WikiClient#deletePageVersion(java.lang.String, int)
	 */
	public  boolean deletePageVersion(String name, int version) throws PageNotFoundException, PageVersionNotFoundException, PermissionDeniedException{
		try {
			return getClient().deletePage(name, version);
		} catch (UndeclaredThrowableException e) {
			String message = e.getUndeclaredThrowable().getMessage();
			if (message != null && message.contains("WIKI_DELETE")) {
				throw new PermissionDeniedException();
			}
			throw e;
		}
	}
	
	
	/**
	 * 
	 */
	public List<PageInfo> getPageHistory(String pageName) throws PageNotFoundException {
		Object[] versions = getClient().getPageVersions(pageName);
		List<PageInfo> history = new ArrayList<PageInfo>();
		for (int i = 0; i < versions.length; i++) {
			Map<String, Object> pageInfo = (Map<String, Object>) versions[i];
			// FIXME implement it as a list of actual PageInfo objects
			history.add(pageInfo2PageVersion(pageInfo, null));
		}
		return history;
	}

	/**
	 * 
	 */
	public List<PageInfo> getRecentChanges(Date since) {
		Object[] returnedChanges = getClient().getRecentChanges(since);
		List<PageInfo> recentChanges = new ArrayList<PageInfo>();
		for (int i = 0; i < returnedChanges.length; i++) {
			Map<String, Object> pageInfo = (Map<String, Object>) returnedChanges[i];
			// FIXME implement it as a list of actual PageInfo objects
			recentChanges.add(pageInfo2PageVersion(pageInfo, null));
		}
		return recentChanges;		
	}

	/**
	 * 
	 */
	public String wikiToHtml(String wikiText) {
		return getClient().wikiToHtml(wikiText);
	}
	
	//----------------
	
	/**
	 * 
	 * @param pageName
	 * @return
	 */
	private Map<String, Object> getPageInfo(String pageName) throws PageNotFoundException{
		Map<String, Object> pageInfo;
		try {
			pageInfo = getClient().getPageInfo(pageName);
		} catch (ClassCastException e) {
			throw new PageNotFoundException();
		}
		return pageInfo;
	}
	
	/**
	 * FIXME comment property is missing from pageInfo
	 * 
	 * @param pageInfo
	 * @return
	 */
	private PageVersion pageInfo2PageVersion(Map<String, Object> pageInfo, String content) {
		PageVersion pageVersion = new PageVersion();
		pageVersion.setName((String) pageInfo.get("name"));
		pageVersion.setVersion((Integer) pageInfo.get("version"));
		pageVersion.setDate((Date) pageInfo.get("lastModified"));
		pageVersion.setAuthor((String) pageInfo.get("author"));
		pageVersion.setComment((String) pageInfo.get("comment"));
		pageVersion.setContent(content);
		return pageVersion;
	}
	
	private void wikiClientPutPage(String name, String content, Map<String, String> attributes) throws PageNotModifiedException {
		try {
			getClient().putPage(name, content, attributes);
		} catch (UndeclaredThrowableException e) {
			Throwable cause = e.getUndeclaredThrowable();
			if(cause  != null 
					&& cause.getMessage() != null 
					&& cause.getMessage().contains("Page not modified") ) 
			{
				throw new PageNotModifiedException();
			}
			else {
				throw e;
			}
		}
	}

}