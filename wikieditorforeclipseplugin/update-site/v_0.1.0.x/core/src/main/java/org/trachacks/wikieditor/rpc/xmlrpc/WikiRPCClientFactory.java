/**
 * 
 */
package org.trachacks.wikieditor.rpc.xmlrpc;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.lang.reflect.UndeclaredThrowableException;
import java.net.MalformedURLException;
import java.net.URL;

import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.ProxyHost;
import org.apache.commons.httpclient.UsernamePasswordCredentials;
import org.apache.commons.httpclient.auth.AuthScope;
import org.apache.commons.httpclient.methods.GetMethod;
import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import org.apache.xmlrpc.client.XmlRpcCommonsTransportFactory;
import org.apache.xmlrpc.common.TypeConverter;
import org.apache.xmlrpc.common.TypeConverterFactory;
import org.apache.xmlrpc.common.TypeConverterFactoryImpl;
import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.GatewayTimeoutException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.ProxyAuthenticationRequiredException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;

/**
 * @author ivan
 * 
 */
public class WikiRPCClientFactory{

	private static int TIMEOUT = 30000;

	private static final TypeConverterFactory typeConverterFactory = new TypeConverterFactoryImpl();


	/**
	 * 
	 * @param server
	 * @param credentials
	 * @return
	 */
	public static WikiRPC getWikiRPCClientInstance(ServerDetails server, ProxySettings proxySettings) {
		return newInstance(WikiRPC.class, server, proxySettings);
	}

	/**
	 * 
	 * @param server
	 * @param credentials
	 * @return
	 */
	private static XmlRpcClientConfigImpl buildConfiguration(ServerDetails server) {
		XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();

		String contextPath = server.isAnonymous() ? WikiRPC.anonymousPath : WikiRPC.authenitcatedPath;
		
		try {
			config.setServerURL(server.appendURL(contextPath));
		} catch (MalformedURLException e) {
			// TODO Handle this (unlikely) exception
			throw new RuntimeException(e);
		}
		
		if( !server.isAnonymous()) {
			config.setBasicUserName(server.getUsername());
			config.setBasicPassword(server.getPassword());
		}
		
		config.setConnectionTimeout(TIMEOUT);
		config.setReplyTimeout(TIMEOUT);
		
		return config;
	}
	

	/**
	 * Creates an object, which is implementing the given interface. The objects
	 * methods are internally calling an XML-RPC server by using the factories
	 * client.
	 */
	@SuppressWarnings("unchecked")
	protected static <T> T newInstance(final Class<T> clazz, ServerDetails server, ProxySettings proxySettings) {
		
		XmlRpcClientConfigImpl config = buildConfiguration(server);
		
		final XmlRpcClient client = new XmlRpcClient();
        client.setConfig(config);
        XmlRpcCommonsTransportFactory transportFactory = new XmlRpcCommonsTransportFactory(client);
        if(proxySettings != null) {
        	transportFactory.setHttpClient(getHttpClient(proxySettings));
        }
        //httpClient.getHostConfiguration().setHost(server.getUrl());
        client.setTransportFactory(transportFactory);
		
		/* create the proxy */
		return (T) Proxy.newProxyInstance(Thread.currentThread().getContextClassLoader(), new Class[] { clazz },
				new InvocationHandler() {
					public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
						if (method.getDeclaringClass().equals(Object.class)) {
							return method.invoke(proxy, args);
						}
						String methodName = method.getDeclaringClass().getSimpleName().toLowerCase() + 
															"." + method.getName();
						Object result = client.execute(methodName, args);
						TypeConverter typeConverter = typeConverterFactory.getTypeConverter(method.getReturnType());
						return typeConverter.convert(result);
					}
				});
	}

	/**
	 * 
	 * @param server
	 * 
	 * @return Returns true if a compatible XML-RPC interface is found, false otherwise.
	 * 
	 * @throws UnknownServerException
	 * @throws ConnectionRefusedException
	 * @throws BadCredentialsException
	 * @throws PermissionDeniedException
	 */
	public static boolean testConnection(ServerDetails server, ProxySettings proxySettings) throws UnknownServerException, ConnectionRefusedException, BadCredentialsException, PermissionDeniedException {
		try {
 			WikiRPC client = WikiRPCClientFactory.getWikiRPCClientInstance(server, proxySettings);
			return client.getRPCVersionSupported() >= WikiRPC.RPC_API_VERSION;
		} catch (UndeclaredThrowableException e) {
			XmlRpcException xmlRpcException = (XmlRpcException) e.getCause();
			Throwable cause = xmlRpcException.linkedException;
			if(cause instanceof java.net.UnknownHostException || cause instanceof java.net.MalformedURLException) {
				throw new UnknownServerException();
			}
			else if(cause instanceof java.net.ConnectException) {
				throw new ConnectionRefusedException();
			}
			else {
				try { /* test for bad credentials or permission denied */
					URL authenticatedURL = server.appendURL(WikiRPC.authenitcatedPath);
					URL anonymousURL = server.appendURL(WikiRPC.anonymousPath);
					
					HttpClient client =  getHttpClient(proxySettings);
					GetMethod get = null;
					int resultCode = 0;
					
					if(!server.isAnonymous()) {
						client.getState().setCredentials(
					            new AuthScope(authenticatedURL.getHost(), authenticatedURL.getPort(), AuthScope.ANY_REALM),
					            new UsernamePasswordCredentials(server.getUsername(), server.getPassword())
					        );
						get = new GetMethod(authenticatedURL.toString());
					}
					else {
						get = new GetMethod(anonymousURL.toString());
					}
					try {
						resultCode = client.executeMethod(get);
					} catch (Exception e1) {
						throw new RuntimeException(e1); // FIXME
					}
					if (resultCode == 401) {/* BadCredentials */
						throw new BadCredentialsException();
					}
					if (resultCode == 403) {/* PermissionDenied */
						throw new PermissionDeniedException();
					}
					if (proxySettings != null ) {
						if( resultCode == 504) { /* Gateway Timeout */
							throw new GatewayTimeoutException();
						}
						if(resultCode == 407) {
							throw new ProxyAuthenticationRequiredException();
						}
					}
				} catch (MalformedURLException ignored) {}
			}
			
			throw new RuntimeException(cause);
		}
	}
	
	/**
	 * 
	 * @param proxySettings
	 * @return
	 */
	private static HttpClient getHttpClient(ProxySettings proxySettings) {
    	HttpClient httpClient = new HttpClient();
    	if(proxySettings != null) {
    		httpClient.getHostConfiguration().setProxy(proxySettings.getProxyHost(), proxySettings.getProxyPort());

    		if(proxySettings.isAuthenticationRequired()) {
    			httpClient.getState().setProxyCredentials(
    					new AuthScope(proxySettings.getProxyHost(), proxySettings.getProxyPort(), AuthScope.ANY_REALM),
    					new UsernamePasswordCredentials(proxySettings.getProxyUsername(), proxySettings.getProxyPassword())
    			);
    		}
    	}
    	return httpClient;
	}

}
