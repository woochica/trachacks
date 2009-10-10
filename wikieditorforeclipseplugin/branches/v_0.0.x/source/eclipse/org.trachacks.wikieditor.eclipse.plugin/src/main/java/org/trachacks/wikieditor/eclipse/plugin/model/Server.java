/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;


import org.eclipse.core.net.proxy.IProxyData;
import org.eclipse.core.net.proxy.IProxyService;
import org.eclipse.core.runtime.Platform;
import org.eclipse.core.runtime.preferences.IEclipsePreferences;
import org.eclipse.core.runtime.preferences.IPreferencesService;
import org.osgi.service.prefs.BackingStoreException;
import org.trachacks.wikieditor.eclipse.plugin.Activator;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.GatewayTimeoutException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.ProxyAuthenticationRequiredException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;
import org.trachacks.wikieditor.service.ServiceFactory;
import org.trachacks.wikieditor.service.WikiService;

/**
 * @author ivan
 *
 */
public class Server extends AbstractBaseObject {

	private List<Page> pages;
	private ServerDetails serverDetails;
	private WikiService wikiService;
	private boolean connected = false;

	/**
	 * @param serverDetails
	 */
	Server(ServerDetails serverDetails) {
		super();
		this.serverDetails = serverDetails;
		ProxySettings proxySettings = getProxySettings(serverDetails);
		this.wikiService = ServiceFactory.getWikiService(serverDetails, proxySettings);
	}

	
	public ServerDetails getServerDetails() {
		return serverDetails;
	}

	void setServerDetails(ServerDetails serverDetails) {
		this.serverDetails = serverDetails;
	}

	/**
	 * 
	 * @return
	 */
	public String[] getPageNames() {
		return getWikiService().getPageNames();
	}

	/**
	 * 
	 * @return
	 */
	public List<Page> getPages() {
		return pages;
	}
	
	/**
	 * @return
	 * @see org.trachacks.wikieditor.service.WikiService#loadPages()
	 */
	private void buildTree() {
		String[] pageNames = getWikiService().getPageNames();
		
		this.pages = buildTree(pageNames);
	}
	
	private List<Page> buildTree(String[] pageNames) {
		Arrays.sort(pageNames);

		List<Page> treePages = new ArrayList<Page>();
		for (int i = 0; i < pageNames.length; i++) {
			String fullname = pageNames[i].toString();
			String[] tokens = fullname.split("/");
			Page parent = null;
			for (int j = 0; j < tokens.length; j++) {
				String nodeName = tokens[j];
				Page currentNode = null;
				Iterable<Page> sibilings = parent != null? parent.getChildren() : treePages; 
				for (Page existingNode : sibilings) {
					if(nodeName.equals(existingNode.getShortName())) {
						currentNode = existingNode;
					}
				}
				if(currentNode == null) {
					String nodePath = nodeName;
					if(parent != null) {
						nodePath = parent.getName() + "/" + nodeName;
					}
					currentNode = new Page(this, nodePath);
					if(parent != null) {
						parent.addChild(currentNode);
					}else {
						treePages.add(currentNode);
					}
				}
				if(j == tokens.length -1) {
					currentNode.setIsFolder(false);
				}
				parent = currentNode;
			}
		}
		
		return treePages;
	}

	/**
	 * 
	 * @param pageName
	 * @return Returns the list o page children
	 */
	List<Page> getPageChildren(String pageName) {
		if(!pageName.endsWith("/")) {
			pageName = pageName + "/";
		}
		String[] pageNames = getWikiService().getPageNames();
		List<String> childrenPageNames = new ArrayList<String>();
		for (int i = 0; i < pageNames.length; i++) {
			String aPageName = pageNames[i];
			if(aPageName.startsWith(pageName) && !aPageName.equals(pageName)) {
				childrenPageNames.add(aPageName);
			}
		}
		
		List<Page> tree = buildTree(childrenPageNames.toArray(new String[childrenPageNames.size()]));
		String[] tokens = pageName.split("/");
		for (int i = 0; i < tokens.length; i++) {
			if(tree != null && !tree.isEmpty()) {
				tree = tree.get(0).getChildren();
			}
		}
		
		return tree;
	}


	/**
	 * @return the connected
	 */
	public boolean isConnected() {
		return connected;
	}


	/**
	 * 
	 * @param username
	 * @param password
	 */
	public void connect(String username, String password) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		serverDetails.setUsername(username);
		serverDetails.setPassword(password);
		connect();
	}
	/**
	 * 
	 */
	public void connect() throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		testConnection(serverDetails);
		this.wikiService = ServiceFactory.getWikiService(serverDetails);
		connected = true;
		buildTree();
		notifyChanged();
	}
	
	public void disconnect() {
		connected = false;
		this.wikiService = null;
		if(!serverDetails.isStoreCredentials()) {
			serverDetails.setUsername(null);
			serverDetails.setPassword(null);
		}
		notifyChanged();
	}
	
	public void refresh() {
		buildTree();
		notifyChanged();
	}


	/**
	 * 
	 * @param name
	 * @return
	 */
	public Page newPage(String name) {
		PageVersion pageVersion = new PageVersion();
		pageVersion.setName(name);
		pageVersion.setServerId(serverDetails.getId());
		pageVersion.setAuthor(serverDetails.getUsername());
		pageVersion.setDate(new Date());
		/* edit */
		getWikiService().edit(pageVersion);
		
		refresh();
		return getPage(name);
	}
	
	/**
	 * @param name
	 * @return
	 * @throws PageNotFoundException
	 * @see org.trachacks.wikieditor.service.WikiService#loadPageVersion(java.lang.String)
	 */
	public Page getPage(String name) throws PageNotFoundException {
		return new Page(this, name);
	}


	public void deletePage(Page page) throws PermissionDeniedException{
		getWikiService().deletePage(page.getName());
		if(page.getParent() != null) {
			page.getParent().refresh();
		}
		notifyChanged();
	}

	public void deletePageVersion(Page page, int version) throws PermissionDeniedException{
		getWikiService().deletePageVersion(page.getName(), version);
		page.notifyChanged();
		notifyChanged();
	}

	
	protected WikiService getWikiService() {
		if(!isConnected()) {
			ConnectionRefusedException e = new ConnectionRefusedException();
			Logger.getLogger(this.getClass().getName()).log(Level.WARNING, "Trying to access server before connecting", e);  //$NON-NLS-1$
			throw e;
		}
		return wikiService;
	}


	/**
	 * 
	 * @param serverDetails
	 * @return
	 * @throws UnknownServerException
	 * @throws ConnectionRefusedException
	 * @throws BadCredentialsException
	 * @throws PermissionDeniedException
	 * @see org.trachacks.wikieditor.service.WikiService#testConnection(ServerDetails)
	 */
	public static boolean testConnection(ServerDetails serverDetails) 
		throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException,
			GatewayTimeoutException, ProxyAuthenticationRequiredException
	{
		ProxySettings proxySettings = getProxySettings(serverDetails);
		return ServiceFactory.getWikiService(serverDetails).testConnection(serverDetails, proxySettings);
	}

	
	private static ProxySettings getProxySettings(ServerDetails serverDetails) {
		IProxyService proxyService = Activator.getDefault().getProxyService();
		IProxyData[] proxyData = proxyService.getProxyDataForHost(serverDetails.getUrl().getHost());
		if(proxyData != null && proxyData.length > 0) {
			return new ProxySettings(proxyData[0].getHost(), proxyData[0].getPort(), 
					proxyData[0].getUserId(), proxyData[0].getPassword());
		}
		else {
			return null;
		}
	}
}
