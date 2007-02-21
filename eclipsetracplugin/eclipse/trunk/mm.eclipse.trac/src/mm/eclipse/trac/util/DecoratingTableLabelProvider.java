/**
 * 
 */
package mm.eclipse.trac.util;

import org.eclipse.core.runtime.ListenerList;
import org.eclipse.jface.util.Assert;
import org.eclipse.jface.viewers.DecorationContext;
import org.eclipse.jface.viewers.IColorDecorator;
import org.eclipse.jface.viewers.IDecorationContext;
import org.eclipse.jface.viewers.IFontDecorator;
import org.eclipse.jface.viewers.ILabelDecorator;
import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.ITableLabelProvider;
import org.eclipse.jface.viewers.LabelDecorator;
import org.eclipse.jface.viewers.ViewerLabel;
import org.eclipse.swt.graphics.Image;

/**
 * @author Matteo Merli
 * 
 */
public class DecoratingTableLabelProvider implements ITableLabelProvider
{
    
    private ITableLabelProvider provider;
    
    private ILabelDecorator     decorator;
    
    // Need to keep our own list of listeners
    private ListenerList        listeners         = new ListenerList();
    
    private IDecorationContext  decorationContext = DecorationContext.DEFAULT_CONTEXT;
    
    public DecoratingTableLabelProvider( ITableLabelProvider provider,
            ILabelDecorator decorator )
    {
        Assert.isNotNull( provider );
        this.provider = provider;
        this.decorator = decorator;
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>IBaseLabelProvider</code> method adds the listener to both the
     * nested label provider and the label decorator.
     * 
     * @param listener
     *            a label provider listener
     */
    public void addListener( ILabelProviderListener listener )
    {
        provider.addListener( listener );
        if ( decorator != null )
        {
            decorator.addListener( listener );
        }
        listeners.add( listener );
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>IBaseLabelProvider</code> method disposes both the nested label
     * provider and the label decorator.
     */
    public void dispose()
    {
        provider.dispose();
        if ( decorator != null )
        {
            decorator.dispose();
        }
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>ILabelProvider</code> method returns the image provided by the
     * nested label provider's <code>getImage</code> method, decorated with
     * the decoration provided by the label decorator's
     * <code>decorateImage</code> method.
     */
    public Image getColumnImage( Object element, int idx )
    {
        Image image = provider.getColumnImage( element, idx );
        if ( decorator != null )
        {
            if ( decorator instanceof LabelDecorator )
            {
                LabelDecorator ld2 = (LabelDecorator) decorator;
                Image decorated = ld2.decorateImage( image, element,
                                                     getDecorationContext() );
                if ( decorated != null )
                {
                    return decorated;
                }
            } else
            {
                Image decorated = decorator.decorateImage( image, element );
                if ( decorated != null )
                {
                    return decorated;
                }
            }
        }
        return image;
    }
    
    /**
     * Returns the label decorator, or <code>null</code> if none has been set.
     * 
     * @return the label decorator, or <code>null</code> if none has been set.
     */
    public ILabelDecorator getLabelDecorator()
    {
        return decorator;
    }
    
    /**
     * Returns the nested label provider.
     * 
     * @return the nested label provider
     */
    public ITableLabelProvider getLabelProvider()
    {
        return provider;
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>ILabelProvider</code> method returns the text label provided by
     * the nested label provider's <code>getText</code> method, decorated with
     * the decoration provided by the label decorator's
     * <code>decorateText</code> method.
     */
    public String getColumnText( Object element, int idx )
    {
        String text = provider.getColumnText( element, idx );
        if ( decorator != null )
        {
            if ( decorator instanceof LabelDecorator )
            {
                LabelDecorator ld2 = (LabelDecorator) decorator;
                String decorated = ld2.decorateText( text, element,
                                                     getDecorationContext() );
                if ( decorated != null )
                {
                    return decorated;
                }
            } else
            {
                String decorated = decorator.decorateText( text, element );
                if ( decorated != null )
                {
                    return decorated;
                }
            }
        }
        return text;
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>IBaseLabelProvider</code> method returns <code>true</code> if
     * the corresponding method on the nested label provider returns
     * <code>true</code> or if the corresponding method on the decorator
     * returns <code>true</code>.
     */
    public boolean isLabelProperty( Object element, String property )
    {
        if ( provider.isLabelProperty( element, property ) )
        {
            return true;
        }
        if ( decorator != null && decorator.isLabelProperty( element, property ) )
        {
            return true;
        }
        return false;
    }
    
    /**
     * The <code>DecoratingLabelProvider</code> implementation of this
     * <code>IBaseLabelProvider</code> method removes the listener from both
     * the nested label provider and the label decorator.
     * 
     * @param listener
     *            a label provider listener
     */
    public void removeListener( ILabelProviderListener listener )
    {
        provider.removeListener( listener );
        if ( decorator != null )
        {
            decorator.removeListener( listener );
        }
        listeners.remove( listener );
    }
 
    
 
    /**
     * Decoration is ready. Update anything else for the settings.
     * 
     * @param settings
     *            The object collecting the settings.
     * @param element
     *            The Object being decorated.
     * @since 3.1
     */
    protected void updateForDecorationReady( ViewerLabel settings, Object element )
    {
        
        if ( decorator instanceof IColorDecorator )
        {
            IColorDecorator colorDecorator = (IColorDecorator) decorator;
            settings.setBackground( colorDecorator.decorateBackground( element ) );
            settings.setForeground( colorDecorator.decorateForeground( element ) );
        }
        
        if ( decorator instanceof IFontDecorator )
        {
            settings.setFont( ((IFontDecorator) decorator).decorateFont( element ) );
        }
        
    }
    
    /**
     * Return the decoration context associated with this label provider. It
     * will be passed to the decorator if the decorator is an instance of
     * {@link LabelDecorator}.
     * 
     * @return the decoration context associated with this label provider
     * 
     * @since 3.2
     */
    public IDecorationContext getDecorationContext()
    {
        return decorationContext;
    }
    
    /**
     * Set the decoration context that will be based to the decorator for this
     * label provider if that decorator implements {@link LabelDecorator}.
     * 
     * @param decorationContext
     *            the decoration context.
     * 
     * @since 3.2
     */
    public void setDecorationContext( IDecorationContext decorationContext )
    {
        Assert.isNotNull( decorationContext );
        this.decorationContext = decorationContext;
    }
    
}
