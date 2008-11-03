/**
 * 
 */
package mm.eclipse.trac.models;

import java.net.URL;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.xmlrpc.Trac;
import mm.eclipse.trac.xmlrpc.Wiki;
import mm.eclipse.trac.xmlrpc.WikiExt;

import org.eclipse.core.runtime.IAdaptable;

/**
 * Trac server model.
 * 
 * @author Matteo Merli
 * 
 */
public class TracServer extends ModelBase implements IAdaptable
{
    
    private URL     url;
    private String  name;
    private String  username;
    private String  password;
    private boolean anonymous;
    
    private boolean connected;
    private boolean problems;
    
    private Trac    trac;
    
    private WikiPage rootWikiPage;
    
    public TracServer( String name, URL url, String username, String password,
                       boolean anonymous )
    {
        this.name = name;
        this.url = url;
        this.username = username;
        this.password = password;
        this.anonymous = anonymous;
        connected = false;
        problems = false;
        
        rootWikiPage = new WikiPage( this, "", 0, true, true );
        rootWikiPage.setRoot( true );
    }
    
    public void connect()
    {
        assert !connected;
        
        try
        {
            trac = new Trac( url, username, password, anonymous );
            connected = true;
            problems = false;
            
        } catch ( Exception e )
        {
            Log.warning( "Error connecting to server '" + url.toString() + "': " + e.getMessage(), e );
            connected = false;
            problems = true;
        }
        
        notifyChanged();
    }
    
    public void disconnect()
    {
        assert connected;
        trac = null;
        connected = false;
        notifyChanged();
    }
    
    /**
     * Test whether the connection with Trac is up.
     * 
     * @return true if the Trac installations is reachable.
     */
    public boolean isValid()
    {
        return !problems;
    }
    
    public Wiki getWiki()
    {
        assert connected;
        return trac.getWiki();
    }
    
    public WikiExt getWikiExt()
    {
        assert connected;
        return trac.getWikiExt();
    }
    
    
    public WikiPage getRootWikiPage()
    {
        return rootWikiPage;
    }
    
    // Accessors:
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.core.runtime.IAdaptable#getAdapter(java.lang.Class)
     */
    public Object getAdapter( Class adapter )
    {
        return null;
    }
    
    /**
     * @return the name
     */
    public String getName()
    {
        return name;
    }
    
    /**
     * @param name
     *            the name to set
     */
    public void setName( String name )
    {
        this.name = name;
        notifyChanged();
    }
    
    /**
     * @return the password
     */
    public String getPassword()
    {
        return password;
    }
    
    /**
     * @param password
     *            the password to set
     */
    public void setPassword( String password )
    {
        this.password = password;
        notifyChanged();
    }
    
    /**
     * @return the url
     */
    public URL getUrl()
    {
        return url;
    }
    
    /**
     * @param url
     *            the url to set
     */
    public void setUrl( URL url )
    {
        this.url = url;
        notifyChanged();
    }
    
    /**
     * @return the username
     */
    public String getUsername()
    {
        return username;
    }
    
    /**
     * @param username
     *            the username to set
     */
    public void setUsername( String username )
    {
        this.username = username;
        notifyChanged();
    }
    
    /**
     * @return the connected
     */
    public boolean isConnected()
    {
        return connected;
    }

    /**
     * @return the anonymous
     */
    public boolean isAnonymous()
    {
        return anonymous;
    }

    /**
     * @param anonymous the anonymous to set
     */
    public void setAnonymous( boolean anonymous )
    {
        this.anonymous = anonymous;
    }
    
}
