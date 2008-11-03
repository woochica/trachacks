package mm.eclipse.trac.models;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.xmlrpc.WikiExt;

import org.eclipse.core.runtime.IAdaptable;

public class WikiPage extends ModelBase implements IAdaptable
{
    private final TracServer server;

    private final String fullName;
    private int version;
    private boolean exists = false;
    private boolean hasChildren = false;
    private List<WikiPage> children = null;
    private WikiPage parent = null;
    private boolean root = false;
    private boolean dirty = false;

    private List<WikiPageVersion> versions = null;

    public WikiPage( TracServer server, String fullName, int version,
            boolean exists )
    {
        this( server, fullName, version, exists, server.getWikiExt()
                .hasChildren( fullName ) );
    }

    public WikiPage( TracServer server, String fullName, int version,
            boolean exists, boolean hasChildren )
    {
        this.server = server;
        this.fullName = fullName;
        this.version = version;
        this.exists = exists;
        this.hasChildren = hasChildren;
        Activator.wikiPageCache().checkPage( this );
    }

    public WikiPage( TracServer server, String fullName )
    {
        this( server, fullName, 0, true );
        Activator.wikiPageCache().checkPage( this );
    }

    /**
     * @return the server
     */
    public TracServer getServer()
    {
        return server;
    }

    /**
     * @return the fullName of the page
     */
    public String getSimpleName()
    {
        String[] path = fullName.split( "/" );
        return path[path.length - 1];
    }

    /**
     * @return wheter the page exists in Trac or if is only a tree node.
     */
    public boolean exists()
    {
        return exists;
    }

    /**
     * @return the fullName of the page
     */
    public String getFullName()
    {
        return fullName;
    }

    public int getVersion()
    {
        return version;
    }

    public void addChild( WikiPage child )
    {
        if ( children == null )
            children = new ArrayList<WikiPage>();

        children.add( child );
        child.parent = this;
        notifyChanged();
    }

    public boolean hasChildren()
    {
        return hasChildren;
    }

    public Collection<WikiPage> getChildren()
    {
        if ( children != null )
            return children;

        children = new ArrayList<WikiPage>();
        WikiExt wikiExt = server.getWikiExt();

        Map<String, Map<String, Object>> childrenMap = wikiExt
                .getChildren( fullName );
        SortedSet<String> names = new TreeSet<String>( childrenMap.keySet() );

        for ( String name : names )
        {
            Map<String, Object> attrs = childrenMap.get( name );
            int version = (Integer) attrs.get( "version" );
            boolean exists = (Boolean) attrs.get( "exists" );
            boolean hasChildren = (Boolean) attrs.get( "hasChildren" );
            children.add( new WikiPage( server, name, version, exists,
                    hasChildren ) );
        }

        return children;
    }

    public WikiPage getParent()
    {
        return parent;
    }

    public String toString()
    {
        return getFullName();
    }

    public InputStream getContent()
    {
        return Activator.wikiPageCache().getPage( this );
    }

    public String getStringContent()
    {
        InputStream is = getContent();

        StringBuilder sb = new StringBuilder();
        try
        {
            while (true)
            {
                char c = (char) is.read();
                if ( c == (char)-1 )
                    break;
                else
                    sb.append( c );
            }
        }
        catch ( IOException e )
        {
            Log.error( "Error reading content", e );
        }

        return sb.toString();
    }

    public void putContent( String content )
    {
        setDirty( true );
        Activator.wikiPageCache().putPage( this, content );
    }

    /**
     * Save the page in the Trac database
     * 
     * @param comment
     *            The comment entry
     */
    public void commit( String comment )
    {
        Map<String, String> attributes = new HashMap<String, String>();
        attributes.put( "comment", comment );
        
        String content = getStringContent();
        server.getWiki().putPage( fullName, content, attributes );

        // Should refresh with newly created version
        version += 1;
        versions = null;
        setDirty( false );
        
        Activator.wikiPageCache().putPage( this, content );
    }

    public List<WikiPageVersion> getVersions()
    {
        if ( versions != null )
            return versions;

        versions = new ArrayList<WikiPageVersion>();
        Object[] remoteVersions = server.getWikiExt()
                .getPageVersions( fullName );

        for ( Object o : remoteVersions )
        {
            Map a = (Map) o;
            WikiPageVersion version;
            version = new WikiPageVersion( this, (Integer) a.get( "version" ),
                    (String) a.get( "author" ), (String) a.get( "comment" ),
                    (Date) a.get( "lastModified" ) );
            versions.add( version );
        }

        return versions;
    }

    public Object getAdapter( Class adapter )
    {
        // // Log.info( "WikiPage.getAdapter: " + adapter.toString() );
        return null;
    }

    public void setRoot( boolean root )
    {
        this.root = root;
    }

    public boolean isRoot()
    {
        return root;
    }

    public boolean isDirty()
    {
        return dirty;
    }

    public void setDirty( boolean dirty )
    {
        this.dirty = dirty;
        notifyChanged();
    }

}
