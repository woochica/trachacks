/**
 * 
 */
package mm.eclipse.trac.models;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;

import org.eclipse.core.runtime.preferences.ConfigurationScope;
import org.eclipse.core.runtime.preferences.IEclipsePreferences;
import org.osgi.service.prefs.BackingStoreException;

/**
 * @author Matteo Merli
 * 
 */
public class TracServerList extends ModelBase implements Iterable<TracServer>
{
    private List<TracServer>    servers;
    
    private static final String CATEGORY = Activator.PLUGIN_ID + ".server";
    
    public List<TracServer> getServers()
    {
        return servers;
    }
    
    public void addServer( TracServer server )
    {
        servers.add( server );
        notifyChanged();
    }
    
    public void removeServer( TracServer server )
    {
        servers.remove( server );
        notifyChanged();
    }
    
    private TracServerList()
    {
        savePreferences();
        loadPreferences();
        
        servers = new ArrayList<TracServer>();
        try
        {
            TracServer server = new TracServer( "Entorno.Tpvs",
                                                new URL( "http://entorno.tpvs/trac" ),
                                                "mme002es", "bjc2100", false );
            servers.add( server );
            
            server = new TracServer( "Otro", new URL( "http://entorsd" ), "mme002es",
                                     "bjc2100", false );
            // servers.add( server );
            
        } catch ( MalformedURLException e )
        {
        }
    }
    
    private void loadPreferences()
    {
        IEclipsePreferences prefs = new ConfigurationScope().getNode( CATEGORY );
        
        String[] keys;
        try
        {
            keys = prefs.childrenNames();
        } catch ( BackingStoreException e )
        {
            Log.error( "BackingStoreException.", e );
            keys = new String[0];
        }
        
        for ( String key : keys )
        {
            IEclipsePreferences node = (IEclipsePreferences) prefs.node( key );
            String value = node.get( "test", "hola" );
            Log.info( "Test: " + value );
        }
    }
    
    private void savePreferences()
    {
    // Activator.getDefault().getPluginPreferences().
    // IEclipsePreferences prefs = new ConfigurationScope().getNode( CATEGORY );
    // // try
    // // {
    // // prefs.removeNode();
    // // } catch ( BackingStoreException e )
    // // {
    // // Log.error( "BackingStoreException.", e );
    // // }
    //        
    // prefs.put( "server1", "primo" );
    // prefs.put( "server2", "secondo" );
    // prefs.put( "server3", "terzo" );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see java.lang.Iterable#iterator()
     */
    public Iterator<TracServer> iterator()
    {
        if ( servers == null ) return null;
        
        return servers.iterator();
    }
    
    public static TracServerList getInstance()
    {
        if ( instance == null ) instance = new TracServerList();
        
        return instance;
    }
    
    private static TracServerList instance;
    
}
