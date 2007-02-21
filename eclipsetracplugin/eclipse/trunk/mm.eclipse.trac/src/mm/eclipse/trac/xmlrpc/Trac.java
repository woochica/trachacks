package mm.eclipse.trac.xmlrpc;

import java.net.URL;

import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import org.apache.xmlrpc.client.XmlRpcLiteHttpTransportFactory;

public class Trac
{
    private DynamicProxy proxy;
    private Wiki         wiki    = null;
    private WikiExt      wikiExt = null;
    
    public Trac( URL url, String username, String password, boolean anonymous )
        throws Exception
    {
        XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
        
        String sUrl = url.toString();
        String sep = sUrl.endsWith( "/" ) ? "" : "/";
        
        config.setServerURL( new URL( sUrl + sep + "login/xmlrpc" ) );
        
        if ( !anonymous )
        {
            // If the user chose not to autheticate anonymously
            // but not provided any password, make sure the authentication
            // will fail, without the system asking credentials with an
            // intrusive dialog.
            if ( username.length() == 0 ) username = "xxxx";
            config.setBasicUserName( username );
            
            if ( password.length() == 0 ) password = "xxxx";
            config.setBasicPassword( password );
        }
        
        config.setGzipCompressing( true );
        
        XmlRpcClient client = new XmlRpcClient();
        client.setConfig( config );
        client.setTransportFactory( new XmlRpcLiteHttpTransportFactory( client ) );
        
        proxy = new DynamicProxy( client );
        
        // Call a method to make sure we can communicate with server
        getWiki().getRPCVersionSupported();
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
    
}
