package mm.eclipse.trac.xmlrpc;

import java.net.MalformedURLException;
import java.net.URL;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.preferences.Preferences;

import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import org.eclipse.core.runtime.Preferences.IPropertyChangeListener;
import org.eclipse.core.runtime.Preferences.PropertyChangeEvent;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.swt.widgets.Shell;

public class Trac implements IPropertyChangeListener
{
    private static Trac  instance = null;
    private DynamicProxy proxy;
    private Wiki         wiki     = null;
    private WikiExt      wikiExt = null;
    private boolean      enabled  = false;
    
    public static Trac getInstance()
    {
        if ( instance == null ) instance = new Trac();
        return instance;
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
    
    public String getServerURL()
    {
        IPreferenceStore store = Activator.getDefault().getPreferenceStore();
        return store.getString( Preferences.ServerURL );
    }
    
    public boolean isEnabled()
    {
        return enabled;
    }
    
    private Trac()
    {
        Activator.getDefault().getPluginPreferences().addPropertyChangeListener( this );
        try
        {
            createProxy();
            wiki = getWiki();
            assert wiki.getRPCVersionSupported() >= 2;
            
        } catch ( Throwable t )
        {
            Log.error( "Cannot create Trac proxy." );// , new Exception(t) );
        }
    }
    
    private void createProxy()
    {
        enabled = false;
        try
        {
            XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
            
            assert Activator.getDefault() != null;
            
            IPreferenceStore store = Activator.getDefault().getPreferenceStore();
            
            String serverUrl = store.getString( Preferences.ServerURL );
            String username = store.getString( Preferences.Username );
            String password = store.getString( Preferences.Password );
            
            try
            {
                String suffix = "login/xmlrpc";
                String sep = serverUrl.endsWith( "/" ) ? "" : "/";
                config.setServerURL( new URL( serverUrl + sep + suffix ) );
            } catch ( MalformedURLException e )
            {
                Shell shell = Activator.getDefault().getShell();
                MessageDialog.openError( shell, "Titolo", "Messaggio" );
                return;
            }
            
            if ( username.length() > 0 ) config.setBasicUserName( username );
            if ( password.length() > 0 ) config.setBasicPassword( password );
            
            XmlRpcClient client = new XmlRpcClient();
            client.setConfig( config );
            
            proxy = new DynamicProxy( client );
            wiki = null;
            wikiExt = null;
            
            wiki = getWiki();
            assert wiki.getRPCVersionSupported() >= 2;
            Log.info( "Trac XMLRPC version: " + wiki.getRPCVersionSupported() );
            
        } catch ( Throwable t )
        {
            Shell shell = Activator.getDefault().getShell();
            MessageDialog.openError( shell, "Titolo", "Messaggio" );
            return;
        }
        
        Log.info( "Trac proxy enabled." );
        enabled = true;
    }
    
    public void propertyChange( PropertyChangeEvent event )
    {
        // Force the reinstance of the proxy
        instance = null;
    }
    
}
