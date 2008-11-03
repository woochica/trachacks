package mm.eclipse.trac;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.ResourceBundle;


import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.text.templates.ContextTypeRegistry;
import org.eclipse.jface.text.templates.persistence.TemplateStore;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.editors.text.templates.ContributionContextTypeRegistry;
import org.eclipse.ui.editors.text.templates.ContributionTemplateStore;
import org.eclipse.ui.plugin.AbstractUIPlugin;
import org.osgi.framework.BundleContext;

/**
 * The activator class controls the plug-in life cycle
 */
public class Activator extends AbstractUIPlugin
{
    
    // The plug-in ID
    public static final String              PLUGIN_ID = "mm.eclipse.trac";
    
    // The shared instance
    private static Activator                plugin;
    
    // Members
    private ResourceBundle                  resourceBundle;
    private ContributionTemplateStore       templateStore;
    private ContributionContextTypeRegistry contextTypeRegistry;
    
    private static WikiPageCache wikiPageCache = new WikiPageCache();
    
    /**
     * The constructor
     */
    public Activator()
    {
        resourceBundle = ResourceBundle
                .getBundle( "mm.eclipse.trac.editors.WikiEditorMessages" );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.plugin.AbstractUIPlugin#start(org.osgi.framework.BundleContext)
     */
    public void start( BundleContext context ) throws Exception
    {
        super.start( context );
        plugin = this;
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.plugin.AbstractUIPlugin#stop(org.osgi.framework.BundleContext)
     */
    public void stop( BundleContext context ) throws Exception
    {
        plugin = null;
        super.stop( context );
    }
    
    /**
     * Returns the shared instance
     * 
     * @return the shared instance
     */
    public static Activator getDefault()
    {
        return plugin;
    }
    
    public static WikiPageCache wikiPageCache()
    {
    	return wikiPageCache;
    }
    
    /**
     * Returns an image descriptor for the image file at the given plug-in
     * relative path
     * 
     * @param path
     *            the path
     * @return the image descriptor
     */
    protected static ImageDescriptor getImageDescriptor( String path )
    {
        return imageDescriptorFromPlugin( PLUGIN_ID, path );
    }
    
    public File getResource( String path )
    {
        try
        {
            Log.info( "Location: " + getBundle() );
            URL url = getBundle().getResource( path );
            return new File( url.getPath() );
            
        } catch ( Exception e )
        {
            throw new RuntimeException( "Can't find relative path:" + path, e );
        }
    }
    
    public ResourceBundle getResourceBundle()
    {
        return resourceBundle;
    }
    
    public ContextTypeRegistry getContextTypeRegistry()
    {
        if ( contextTypeRegistry == null )
        {
            contextTypeRegistry = new ContributionContextTypeRegistry();
            contextTypeRegistry.addContextType( "mm.eclipse.trac.templates" );
        }
        return contextTypeRegistry;
    }
    
    public TemplateStore getTemplateStore()
    {
        if ( templateStore == null )
        {
            templateStore = new ContributionTemplateStore( getContextTypeRegistry(),
                                                           getDefault()
                                                                   .getPreferenceStore(),
                                                           "templates" );
            try
            {
                templateStore.load();
            } catch ( IOException e )
            {
                Log.error( "Error loading template store", e );
            }
        }
        
        return templateStore;
    }
    
    public Shell getShell()
    {
        return getWorkbench().getActiveWorkbenchWindow().getShell();
    }
    
}
