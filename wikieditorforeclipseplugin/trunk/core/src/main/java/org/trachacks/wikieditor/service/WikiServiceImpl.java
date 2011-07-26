/**
 * 
 */
package org.trachacks.wikieditor.service;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.trachacks.wikieditor.disk.DiskCache;
import org.trachacks.wikieditor.disk.impl.DiskCacheImpl;
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
import org.trachacks.wikieditor.rpc.WikiClient;
import org.trachacks.wikieditor.rpc.WikiClientImpl;

/**
 * @author ivan
 *
 */
public class WikiServiceImpl implements WikiService{

	private ServerDetails server;
	private WikiClient wikiClient;
	private DiskCache diskCache;
	
	
	public WikiServiceImpl(ServerDetails server, File cacheFolder) {
		this.server = server;
		this.wikiClient = new WikiClientImpl(server);
		this.diskCache =new DiskCacheImpl(cacheFolder);
	}
	
	public WikiServiceImpl(ServerDetails server, File cacheFolder, ProxySettings proxySettings) {
		this.server = server;
		this.wikiClient = new WikiClientImpl(server, proxySettings);
		this.diskCache =new DiskCacheImpl(cacheFolder);
	}
	
	/**
	 * 
	 */
	public boolean testConnection(ServerDetails server) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		return testConnection(server, null);
	}
	
	/**
	 * 
	 */
	public boolean testConnection(ServerDetails server, ProxySettings proxySettings)	throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException, 
														GatewayTimeoutException, ProxyAuthenticationRequiredException
	{
		return wikiClient.testConnection(server, proxySettings);
	}


	/**
	 * 
	 * @return
	 */
	public List<PageInfo> loadPages() {
		String[] pageNames = wikiClient.getPageNames();
		List<PageInfo> pages = new ArrayList<PageInfo>();
		for (int i = 0; i < pageNames.length; i++) {
			String pageName = pageNames[i];
			pages.add(loadPageVersion(pageName));
		}
		return pages;
	}
	
	/**
	 * 
	 */
	public String[] getPageNames() {
		String[] wikiPages = wikiClient.getPageNames();
		String[] cachedNames = diskCache.getCachedPageNames(server.getId());
		
		Set<String> pageNamesList = new HashSet<String>();
		pageNamesList.addAll(Arrays.asList(wikiPages));
		pageNamesList.addAll(Arrays.asList(cachedNames));
		String[] pageNames = pageNamesList.toArray(new String[pageNamesList.size()]);
		Arrays.sort(pageNames);
		
		return pageNames;
	}
	
	/**
	 * 
	 */
	public boolean isLocallyEdited(String pageName) {
		return diskCache.load(server.getId(), pageName) != null;
	}
	
	/**
	 * 
	 * @param pageName
	 * @return
	 * @throws PageNotFoundException
	 */
	public PageVersion loadPageVersion(String pageName){
		// try cachewikiClient.getPageNames();
		PageVersion pageVersion = diskCache.load(server.getId(), pageName);
		if(pageVersion == null) {
			try {
				// try wiki
				pageVersion = wikiClient.getPageVersion(pageName);
			} catch (PageNotFoundException e) {
				// create new page
				pageVersion = new PageVersion();
				pageVersion.setName(pageName);
				pageVersion.setContent("");
				pageVersion.setServerId(server.getId());
				pageVersion.setAuthor(server.getUsername());
			}
			pageVersion.setServerId(server.getId());
		}
		return pageVersion;
	}
	
	/**
	 * 
	 * @param pageVersion
	 * @return
	 */
	public PageVersion edit(PageVersion pageVersion){
		pageVersion.setEdited(true);
		diskCache.save(pageVersion);
		return pageVersion;
	}
	
	/**
	 * 
	 * @param pageVersion
	 * @return
	 * @throws ConcurrentEditException
	 */
	public PageVersion commit(PageVersion pageVersion) throws ConcurrentEditException, PageNotModifiedException {
		return commit(pageVersion, false);
	}
	
	/**
	 * 
	 * @param pageVersion
	 * @return
	 * @throws ConcurrentEditException
	 */
	public PageVersion commit(PageVersion pageVersion, boolean isMinorEdit) throws ConcurrentEditException, PageNotModifiedException{
		wikiClient.savePageVersion(pageVersion.getName(), pageVersion.getContent(), pageVersion.getComment(), pageVersion.getVersion(), isMinorEdit);
		diskCache.remove(pageVersion.getServerId(), pageVersion.getName());
		return wikiClient.getPageVersion(pageVersion.getName());
	}
	
	/**
	 * 
	 * @param pageVersion
	 * @return
	 */
	public PageVersion unedit(PageVersion pageVersion){
		diskCache.remove(pageVersion.getServerId(),pageVersion.getName());
		return wikiClient.getPageVersion(pageVersion.getName());
	}

	/**
	 * 
	 * @param pageVersion
	 * @return
	 */
	public PageVersion forceCommit(PageVersion pageVersion) throws PageNotModifiedException{
		wikiClient.savePageVersion(pageVersion.getName(), pageVersion.getContent(), pageVersion.getComment());
		diskCache.remove(pageVersion.getServerId(),pageVersion.getName());
		return wikiClient.getPageVersion(pageVersion.getName());
	}

	/**
	 * 
	 */
	public PageVersion getLatestVersion(String pageName) throws PageNotFoundException {
		return wikiClient.getPageVersion(pageName);
	}
	
	/**
	 * 
	 */
	public  boolean deletePage(String name) throws PageNotFoundException, PermissionDeniedException {
		diskCache.remove(server.getId(), name);
		return wikiClient.deletePage(name);
	}
	
	/**
	 * 
	 */
	public  boolean deletePageVersion(String name, int version) throws PageNotFoundException, PageVersionNotFoundException, PermissionDeniedException {
		PageVersion cachedVersion = diskCache.load(server.getId(), name);
		if(cachedVersion != null && cachedVersion.getVersion() == version) {
			diskCache.remove(server.getId(), name);
		}
		return wikiClient.deletePageVersion(name, version);
	}
	
	
	/**
	 * 
	 */
	public List<PageInfo> getRecentChanges(Date since) {
		if(since == null) {
			since = new Date(0); // XXX return all changes since epoc
		}
		return wikiClient.getRecentChanges(since);
	}
	/**
	 * 
	 * @param pageName
	 * @return
	 * @throws PageNotFoundException
	 */
	public List<PageInfo> getPageHistory(String pageName) throws PageNotFoundException{
		return wikiClient.getPageHistory(pageName);
	}
	
	/**
	 * 
	 * @param pageName
	 * @param version
	 * @return
	 * @throws PageNotFoundException
	 * @throws PageVersionNotFoundException
	 */
	public PageVersion loadPageVersion(String pageName, int version) throws PageNotFoundException,PageVersionNotFoundException{
		return wikiClient.getPageVersion(pageName, version);
	}

	/**
	 * 
	 */
	public String wikiToHtml(String wikiText) {
		return wikiClient.wikiToHtml(wikiText);
	}
}
