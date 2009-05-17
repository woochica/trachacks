/**
 * 
 */
package org.trachacks.wikieditor.disk.impl;

import java.io.File;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.apache.commons.lang.math.NumberUtils;
import org.trachacks.wikieditor.disk.DiskCache;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

/**
 * @author ivan
 *
 */
public class DiskCacheImpl implements DiskCache {

	private File cacheFolder;

	/**
	 * @param cacheFolder
	 */
	public DiskCacheImpl(File cacheFolder) {
		super();
		this.cacheFolder = cacheFolder;
		if(!cacheFolder.exists()) {
			cacheFolder.mkdirs();
		}
	}
	

	/**
	 * 
	 * @return
	 * @throws Exception
	 */
	@SuppressWarnings("unchecked")
	public Set<ServerDetails> loadServers(){
		Set<ServerDetails> servers = new HashSet<ServerDetails>();
		File file = new File(cacheFolder.getAbsolutePath(), "servers.xml"); //$NON-NLS-1$
		
		if(file.exists() && file.canRead()) {
			Element rootElement = SerializationUtils.loadRootElement(file);
			NodeList list = rootElement.getChildNodes();
			int length = list.getLength();
			for (int i = 0; i < length; ++i) {
				Node node = list.item(i);
				short type = node.getNodeType();
				if (type == Node.ELEMENT_NODE) {
					Element element = (Element) node;
					String nodeName = element.getNodeName();
					if (nodeName.equals("server")) { //$NON-NLS-1$
						String id = element.getAttribute("id"); //$NON-NLS-1$
						String name = element.getAttribute("name"); //$NON-NLS-1$
						String sUrl = element.getAttribute("url"); //$NON-NLS-1$
						String sStoreCredentials = element.getAttribute("storeCredentials"); //$NON-NLS-1$
						String username = element.getAttribute("username"); //$NON-NLS-1$
						String password = element.getAttribute("password"); //$NON-NLS-1$
						URL url = null;
						try {
							url = new URL(sUrl);
						} catch (MalformedURLException e) {
							e.printStackTrace();
						}
						boolean isStoreCredentials = Boolean.parseBoolean(sStoreCredentials);
						ServerDetails serverDetails = null;
						if(isStoreCredentials) { 
							serverDetails = new ServerDetails(Long.parseLong(id), name, url, username, password);
						}else {
							serverDetails = new ServerDetails(Long.parseLong(id), name, url);
						}
						serverDetails.setStoreCredentials(isStoreCredentials);
						servers.add(serverDetails);
					}
				}
			}
		}
		
		return servers;
	}
	
	/**
	 * 
	 * @param servers
	 */
	public void save(Set servers) {
		File file = new File(cacheFolder.getAbsolutePath(), "servers.xml"); //$NON-NLS-1$
		SerializationUtils.serialize(file, servers, new ISerializer() { //$NON-NLS-1$
			public void serialize(Document document, Object object) {
				Element xmlList = document.createElement("serverList"); //$NON-NLS-1$
				document.appendChild(xmlList);
				for(ServerDetails server : (Set<ServerDetails>)object){				
					Element serverElement = document.createElement("server");//$NON-NLS-1$
					serverElement.setAttribute("id", server.getId().toString()); //$NON-NLS-1$
					serverElement.setAttribute("name", server.getName()); //$NON-NLS-1$
					serverElement.setAttribute("url", server.getUrl().toString()); //$NON-NLS-1$
					serverElement.setAttribute("storeCredentials", Boolean.toString(server.isStoreCredentials())); //$NON-NLS-1$
					if(server.isStoreCredentials() && !server.isAnonymous()) {
						serverElement.setAttribute("username", server.getUsername()); //$NON-NLS-1$
						serverElement.setAttribute("password", server.getPassword()); //$NON-NLS-1$
					}
					xmlList.appendChild(serverElement);
				}
			}
			
		});
	}


	/**
	 * 
	 */
	public String[] getCachedPageNames(Long serverId) {
		List<String> pageNames = new ArrayList<String>();
		File[] files = getCacheFiles(serverId);
		for (int i = 0; i < files.length; i++) {
			Element rootElement= SerializationUtils.loadRootElement(files[i]);
			if("pageVersion".equals(rootElement.getNodeName())) {
				pageNames.add(files[i].getName());
			}
		}
		return pageNames.toArray(new String[pageNames.size()]);
	}
	
	/**
	 * 
	 */
	public PageVersion load(Long serverId,String pageName) {
		PageVersion pageVersion = null;
		File file = getPageCacheFile(serverId, pageName);
		if(file.exists()) {
			Element rootElement= SerializationUtils.loadRootElement(file);
			if("pageVersion".equals(rootElement.getNodeName())) {  //$NON-NLS-1$
				pageVersion = new PageVersion();
				pageVersion.setServerId(serverId);
				pageVersion.setName(pageName);
				pageVersion.setContent(rootElement.getTextContent());
				pageVersion.setComment(rootElement.getAttribute("comment"));  //$NON-NLS-1$
				pageVersion.setAuthor(rootElement.getAttribute("author"));  //$NON-NLS-1$
				String version = rootElement.getAttribute("version");  //$NON-NLS-1$
				if(NumberUtils.isNumber(version)) {
					pageVersion.setVersion(Integer.parseInt(version));
				}
				String date = rootElement.getAttribute("date");  //$NON-NLS-1$
				if(NumberUtils.isNumber(date)) {
					pageVersion.setDate(new Date(Long.parseLong(date)));
				}
				pageVersion.setEdited(true);
			}
		}
		return pageVersion;
	}


	/**
	 * 
	 */
	public void remove(Long serverId, String pageName) {
		File file = getPageCacheFile(serverId, pageName);
		if(file.exists()) {
			file.delete();
		}
	}


	/**
	 * 
	 */
	public void save(final PageVersion pageVersion) {
		File file = getPageCacheFile(pageVersion.getServerId(), pageVersion.getName());
		SerializationUtils.serialize(file, pageVersion, new ISerializer() {

			public void serialize(Document document, Object object) {
				Element pageElement = document.createElement("pageVersion");  //$NON-NLS-1$
				document.appendChild(pageElement);
				pageElement.setAttribute("serverId", String.valueOf(pageVersion.getServerId()));  //$NON-NLS-1$
				pageElement.setAttribute("name", pageVersion.getName());  //$NON-NLS-1$
				if(pageVersion.getVersion() != null) {
					pageElement.setAttribute("version", pageVersion.getVersion().toString());  //$NON-NLS-1$
				}
				if(pageVersion.getDate() != null) {
					pageElement.setAttribute("date", String.valueOf(pageVersion.getDate().getTime()));  //$NON-NLS-1$
				}
				pageElement.setAttribute("author", pageVersion.getAuthor());  //$NON-NLS-1$
				pageElement.setAttribute("comment", pageVersion.getComment());  //$NON-NLS-1$
				
				pageElement.setTextContent(pageVersion.getContent());
			}
			
		});
		
	}
	
	private File[] getCacheFiles(Long serverId) {
		File cacheFolder = new File(getServerFolder(serverId).getAbsolutePath());
		if(cacheFolder.exists() && cacheFolder.isDirectory()) {
			return cacheFolder.listFiles();
		}
		return new File[0];
	}
	
	private File getPageCacheFile(Long serverId, String  pageName) {
		return new File(getServerFolder(serverId).getAbsolutePath(), pageName);
	}
	
	private File getServerFolder(Long serverId) {
		File folder = new File(cacheFolder.getAbsolutePath(), String.valueOf(serverId));
		if(!folder.exists()) {
			folder.mkdirs();
		}
		return folder;
	}
}