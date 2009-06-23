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

import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;
import org.trachacks.wikieditor.service.ServiceFactory;
import org.trachacks.wikieditor.service.WikiService;

/**
 * @author ivan
 *
 */
public class Server extends AbstractBaseObject {

	private ServerDetails serverDetails;
	private WikiService wikiService;
	private boolean connected = false;

	/**
	 * @param serverDetails
	 */
	Server(ServerDetails serverDetails) {
		super();
		this.serverDetails = serverDetails;
		this.wikiService = ServiceFactory.getWikiService(serverDetails);
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
	 * @return
	 * @see org.trachacks.wikieditor.service.WikiService#loadPages()
	 */
	public List<Page> getPages() {
		List<Page> pages = new ArrayList<Page>();
		String[] pageNames = getWikiService().getPageNames();

		Arrays.sort(pageNames);
		for (int i = 0; i < pageNames.length; i++) {
			String fullname = pageNames[i].toString();
			String[] tokens = fullname.split("/");
			Page parent = null;
			for (int j = 0; j < tokens.length; j++) {
				String nodeName = tokens[j];
				Page currentNode = null;
				Iterable<Page> sibilings = parent != null? parent.getChildren() : pages; 
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
						pages.add(currentNode);
					}
				}
				if(j == tokens.length -1) {
					currentNode.setIsFolder(false);
				}
				parent = currentNode;
			}
		}

		return pages;
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
		
		notifyChanged();
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
		page.notifyChanged();
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
	public static boolean testConnection(ServerDetails serverDetails) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		return ServiceFactory.getWikiService(serverDetails).testConnection(serverDetails);
	}


}
