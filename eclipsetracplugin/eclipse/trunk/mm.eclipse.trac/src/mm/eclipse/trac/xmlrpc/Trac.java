package mm.eclipse.trac.xmlrpc;

import java.net.URL;
import java.security.cert.X509Certificate;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import mm.eclipse.trac.Log;

import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import org.apache.xmlrpc.client.XmlRpcCommonsTransportFactory;

public class Trac
{
    private DynamicProxy proxy;
    private Wiki         wiki    = null;
    private WikiExt      wikiExt = null;
    
    public Trac( URL url, String username, String password, boolean anonymous )
            throws Exception
    {
        installSslCertificateHandler();
        
        XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
        
        String sUrl = url.toString();
        String sep = sUrl.endsWith( "/" ) ? "" : "/";
        String path;
        if ( anonymous )
            path = "xmlrpc";
        else
            path = "login/xmlrpc";
        
        config.setServerURL( new URL( sUrl + sep + path ) );
        
        if ( !anonymous )
        {
            // If the user chose not to authenticate anonymously
            // but not provided any password, make sure the authentication
            // will fail, without the system asking credentials with an
            // intrusive dialog.
            if ( username.length() == 0 )
                username = "xxxx";
            config.setBasicUserName( username );
            
            if ( password.length() == 0 )
                password = "xxxx";
            config.setBasicPassword( password );
        }
        
        // config.setGzipCompressing( true );
        
        XmlRpcClient client = new XmlRpcClient();
        client.setConfig( config );
        client.setTransportFactory( new XmlRpcCommonsTransportFactory( client ) );
        
        proxy = new DynamicProxy( client );
        Log.info( "Created dynamic proxy" );
        
        // Call a method to make sure we can communicate with server
        client.execute( "wiki.getRPCVersionSupported", new Object[0] );
        getWiki();
        Log.info( "Wiki instantiation ok." );
        getWiki().getRPCVersionSupported();
        Log.info( "Method call ok" );
    }
    
    public Wiki getWiki()
    {
        if ( wiki == null )
        {
            wiki = (Wiki) proxy.newInstance( Wiki.class );
        }
        return wiki;
    }
    
    public WikiExt getWikiExt()
    {
        if ( wikiExt == null )
        {
            wikiExt = (WikiExt) proxy.newInstance( WikiExt.class );
        }
        return wikiExt;
    }
    
    private void installSslCertificateHandler()
    {
        // Create a trust manager that does not validate certificate chains
        
        TrustManager[] trustAllCerts = new TrustManager[] { new X509TrustManager() {
            public X509Certificate[] getAcceptedIssuers()
            {
                return null;
            }
            
            public void checkClientTrusted( X509Certificate[] certs, String authType )
            {
                // Trust always
            }
            
            public void checkServerTrusted( X509Certificate[] certs, String authType )
            {
                // Trust always
            }
        } };
        
        // Install the all-trusting trust manager
        try
        {
            SSLContext sc = SSLContext.getInstance( "SSL" );
            
            // Create empty HostnameVerifier
            HostnameVerifier hv = new HostnameVerifier() {
                public boolean verify( String arg0, SSLSession arg1 )
                {
                    return true;
                }
            };
            
            sc.init( null, trustAllCerts, new java.security.SecureRandom() );
            HttpsURLConnection.setDefaultSSLSocketFactory( sc.getSocketFactory() );
            HttpsURLConnection.setDefaultHostnameVerifier( hv );
            
        } catch ( Exception e )
        {
            Log.error( "Error installing SSL handler", e );
        }
        
        
    }
}
