/*******************************************************************************
 * Copyright (c) 2006 IBM Corporation and others. All rights reserved. This
 * program and the accompanying materials are made available under the terms of
 * the Eclipse Public License v1.0 which accompanies this distribution, and is
 * available at http://www.eclipse.org/legal/epl-v10.html
 * 
 * Contributors: IBM Corporation - initial API and implementation
 ******************************************************************************/
package mm.eclipse.trac.views;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.viewers.IDecoration;
import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.ILightweightLabelDecorator;

/**
 * An example showing how to control when an element is decorated. This example
 * decorates only elements that are instances of IResource and whose attribute
 * is 'Read-only'.
 * 
 * @see ILightweightLabelDecorator
 */
public class TracLabelDecorator implements ILightweightLabelDecorator
{
    
    /** The integer value representing the placement options */
    private static int      quadrant = IDecoration.BOTTOM_RIGHT;
    
    /** The icon image location in the project folder */
    private static String   iconPath = "icons/modified.png";
                                                                 
    /**
     * The image description used in
     * <code>addOverlay(ImageDescriptor, int)</code>
     */
    private ImageDescriptor descriptor = Activator.getImageDescriptor( iconPath );
    
    public void decorate( Object element, IDecoration decoration )
    {
        WikiPage page = (WikiPage)element;
        if ( page.isDirty() )
        {
            decoration.addOverlay( descriptor, quadrant );
        }
    }
    
    public void addListener( ILabelProviderListener listener )
    {}
    
    public void dispose()
    {}
    
    public boolean isLabelProperty( Object element, String property )
    {
        return false;
    }
    
    public void removeListener( ILabelProviderListener listener )
    {}
}
