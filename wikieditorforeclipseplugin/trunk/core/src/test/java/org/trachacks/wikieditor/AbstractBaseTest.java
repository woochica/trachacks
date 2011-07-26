/**
 * 
 */
package org.trachacks.wikieditor;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.MissingResourceException;
import java.util.ResourceBundle;

import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public abstract class AbstractBaseTest {

	private static ResourceBundle baseBundle = ResourceBundle
		.getBundle(AbstractBaseTest.class.getPackage().getName() + ".base");;
	private ResourceBundle bundle = null;
	
	
	protected ProxySettings proxySettings;
	
	/**
	 * 
	 * @param key
	 * @return
	 */
	protected String getSetting(String key) {
		try {
			return bundle.getString(key);
		}catch(Exception e) {}
		try {
			return baseBundle.getString(key);
		}catch(Exception e) {}
		return null;
	}
	
	protected final ServerDetails getTestServer() throws MalformedURLException {
		ServerDetails server = new ServerDetails();
		server.setUrl(new URL(getSetting("server.url")));
		
		server.setUsername(getSetting("credentials.username"));
		server.setPassword(getSetting("credentials.password"));
		
		return server;
	}
	
	protected final void loadProxySettings() {
		String host = getSetting("proxy.host");
		String port = getSetting("proxy.port");
		String username = getSetting("proxy.username");
		String password = getSetting("proxy.password");
		proxySettings = new ProxySettings(host, Integer.parseInt(port), username, password);
	}

}
