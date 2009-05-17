/**
 * 
 */
package org.trachacks.wikieditor.model;

import java.net.MalformedURLException;
import java.net.URL;

import org.apache.commons.lang.StringUtils;

/**
 * @author ivan
 *
 */
public class ServerDetails extends AbstractBaseObject {

	public static String WIKI_VIEW = "WIKI_VIEW";
	public static String WIKI_ADMIN = "WIKI_ADMIN";
	
	private Long id;
    private URL url;
    private String name;
    private boolean storeCredentials = true;
	private String username;
	private String password;
    
	public ServerDetails() {
		super();
	}

	/**
	 * 
	 * @param id
	 * @param name
	 * @param url
	 */
	public ServerDetails(Long id, String name, URL url) {
		super();
		this.id =id;
		this.name = name;
		this.url = url;
	}

	/**
	 * 
	 * @param id
	 * @param name
	 * @param url
	 * @param username
	 * @param password
	 */
	public ServerDetails(Long id, String name, URL url, String username, String password) {
		super();
		this.id = id;
		this.name = name;
		this.url = url;
		this.username = username;
		this.password = password;
	}

	public boolean isNew() {
		return getId() == null;
	}
	
	public URL appendURL(String path) throws MalformedURLException {
		String separator = url.toString().endsWith("/") ? "" : "/";
		String baseURL = url.toString() + separator;
		if(path == null ) {
			return new URL(baseURL);
		}
		else if(path.startsWith("/")) {
			return new URL(baseURL + path.substring(1));
		}
		else {
			return new URL(baseURL + path);
		}
	}
	
	public Long getId() {
		return id;
	}
	public URL getUrl() {
		return url;
	}
	public String getName() {
		return name;
	}
	public boolean isStoreCredentials() {
		return storeCredentials;
	}

	public String getUsername() {
		return username;
	}

	public String getPassword() {
		return password;
	}

	public void setId(Long id) {
		this.id = id;
	}
	public void setUrl(URL url) {
		this.url = url;
	}
	public void setName(String name) {
		this.name = name;
	}
	public void setStoreCredentials(boolean storeCredentials) {
		this.storeCredentials = storeCredentials;
	}
	public void setUsername(String username) {
		this.username = username;
	}
	public void setPassword(String password) {
		this.password = password;
	}

	public boolean isAnonymous() {
		return StringUtils.isBlank(username);
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((id == null) ? 0 : id.hashCode());
		return result;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (!(obj instanceof ServerDetails))
			return false;
		ServerDetails other = (ServerDetails) obj;
		if (id == null) {
			if (other.id != null)
				return false;
		} else if (!id.equals(other.id))
			return false;
		return true;
	}



    
	
}
