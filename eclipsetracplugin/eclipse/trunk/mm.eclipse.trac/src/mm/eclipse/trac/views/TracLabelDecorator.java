/*******************************************************************************
 * Copyright (c) 2006 IBM Corporation and others. All rights reserved. This
 * program and the accompanying materials are made available under the terms of
 * the Eclipse Public License v1.0 which accompanies this distribution, and is
 * available at http://www.eclipse.org/legal/epl-v10.html
 * 
 * Contributors: IBM Corporation - initial API and implementation
 ******************************************************************************/
package mm.eclipse.trac.views;

import mm.eclipse.trac.Images;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.WikiPage;

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
    
    public void decorate( Object element, IDecoration decoration )
    {
        if ( element instanceof TracServer )
        {
            TracServer server = (TracServer) element;
            if ( !server.isValid() )
                decoration.addOverlay( Images.getDescriptor( Images.Error ),
                                       IDecoration.TOP_LEFT );
            
        }
        else if ( element instanceof WikiPage )
        {
            WikiPage page = (WikiPage) element;
            if ( page.isDirty() )
            {
                decoration.addOverlay( Images.getDescriptor( Images.Modified ),
                                       IDecoration.BOTTOM_RIGHT );
            }
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
