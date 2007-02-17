package mm.eclipse.trac.models;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;

import mm.eclipse.trac.xmlrpc.Trac;
import mm.eclipse.trac.xmlrpc.WikiExt;

import org.eclipse.core.runtime.IAdaptable;

public class WikiPage extends ModelBase implements IAdaptable
{
    private String                fullName;
    private boolean               exists      = false;
    private boolean               hasChildren = false;
    private List<WikiPage>        children    = null;
    private WikiPage              parent      = null;
    private boolean               root        = false;
    private boolean               dirty       = false;
    private String                content     = null;
    
    private List<WikiPageVersion> versions    = null;
    
    public WikiPage( String fullName, boolean exists )
    {
        this.fullName = fullName;
        this.exists = exists;
        
        WikiExt wikiExt = Trac.getInstance().getWikiExt();
        this.hasChildren = wikiExt.hasChildren( fullName );
    }
    
    public WikiPage( String fullName, boolean exists, boolean hasChildren )
    {
        this.fullName = fullName;
        this.exists = exists;
        this.hasChildren = hasChildren;
    }
    
    public WikiPage( String fullName )
    {
        this( fullName, true );
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
    
    public void addChild( WikiPage child )
    {
        if ( children == null )
            children = new ArrayList<WikiPage>();
        
        children.add( child );
        child.parent = this;
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
        WikiExt wikiExt = Trac.getInstance().getWikiExt();
        
        Map<String, Map<String, Boolean>> childrenMap = wikiExt.getChildren( fullName );
        SortedSet<String> names = new TreeSet<String>( childrenMap.keySet() );
        
        for ( String name : names )
        {
            Map<String, Boolean> attrs = childrenMap.get( name );
            boolean exists = attrs.get( "exists" );
            boolean hasChildren = attrs.get( "hasChildren" );
            children.add( new WikiPage( name, exists, hasChildren ) );
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
    
    public String getContent()
    {
        if ( content == null )
            content = Trac.getInstance().getWiki().getPage( fullName );
        return content;
    }
    
    public void putContent( String content )
    {
        this.content = content;
        setDirty( true );
        // TODO: Should cache the content on local disk
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
        Trac.getInstance().getWiki().putPage( fullName, content, attributes );
        
        // Should refresh with newly created version
        versions = null;
        
        setDirty( false );
    }
    
    public List<WikiPageVersion> getVersions()
    {
        if ( versions != null )
            return versions;
        
        versions = new ArrayList<WikiPageVersion>();
        Object[] remoteVersions = Trac.getInstance().getWikiExt()
                .getPageVersions( fullName );
        
        for ( Object o : remoteVersions )
        {
            Map a = (Map) o;
            WikiPageVersion version;
            version = new WikiPageVersion( this, (Integer) a.get( "version" ), (String) a
                    .get( "author" ), (String) a.get( "comment" ), (Date) a
                    .get( "lastModified" ) );
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
