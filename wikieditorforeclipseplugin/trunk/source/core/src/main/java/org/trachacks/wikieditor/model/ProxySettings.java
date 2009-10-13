/**
 * 
 */
package org.trachacks.wikieditor.model;

import org.apache.commons.lang.StringUtils;

/**
 * @author ivan
 *
 */
public class ProxySettings extends AbstractBaseObject {

	
	private String proxyHost;
	private Integer proxyPort;
	private String proxyUsername;
	private String proxyPassword;
	private boolean authenticationRequired = false;
	
	public ProxySettings(String proxyHost, Integer proxyPort) {
		super();
		this.proxyHost = proxyHost;
		this.proxyPort = proxyPort;
	}

	public ProxySettings(String proxyHost, Integer proxyPort,
			String proxyUsername, String proxyPassword) {
		super();
		this.proxyHost = proxyHost;
		this.proxyPort = proxyPort;
		this.proxyUsername = proxyUsername;
		this.proxyPassword = proxyPassword;
		this.authenticationRequired = StringUtils.isNotBlank(proxyUsername);
	}


	public String getProxyHost() {
		return proxyHost;
	}
	public Integer getProxyPort() {
		return proxyPort;
	}
	public String getProxyUsername() {
		return proxyUsername;
	}
	public String getProxyPassword() {
		return proxyPassword;
	}

	public boolean isAuthenticationRequired() {
		return authenticationRequired;
	}	
	
}
