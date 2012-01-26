/**
 * 
 */
package org.trachacks.wikieditor.rpc.xmlrpc;

/**
 * @author ivan
 *
 */
public interface WikiRPC extends  Wiki, WikiExt{

	public static final String anonymousPath = "xmlrpc";
	public static final String authenitcatedPath = "login/xmlrpc";
	
}
