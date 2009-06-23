/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation;

import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.swt.graphics.Image;
import org.eclipse.ui.ISharedImages;
import org.eclipse.ui.PlatformUI;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.model.ServerList;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;

/**
 * @author ivan
 *
 */
public class NavigatorLabelProvider extends LabelProvider {

	/**
	 * @see org.eclipse.jface.viewers.LabelProvider#getImage(java.lang.Object)
	 */
	@Override
	public Image getImage(Object element) {
        if (element instanceof Server) {
            return Images.get(((Server)element).isConnected() ? 
            		Images.SERVER_CONNECTED : Images.SERVER_DISCONNECTED);
        }
        else if ( element instanceof Page ) {
        	if(((Page) element).isFolder()) {
        		return Images.get(Images.FOLDER);
        	} else {
        		return Images.get(Images.TEMPLATE);
        	}
        }
        
		return PlatformUI.getWorkbench().getSharedImages()
						.getImage(ISharedImages.IMG_OBJ_ELEMENT);
	}

	/**
	 * @see org.eclipse.jface.viewers.LabelProvider#getText(java.lang.Object)
	 */
	@Override
	public String getText(Object element) {
		if(element instanceof ServerList) {
			return Labels.getText("navigatorLabelProvider.serverList.label");  //$NON-NLS-1$
		}
		else if(element instanceof Server) {
			return ((Server) element).getServerDetails().getName();
		}
		else if(element instanceof Page) {
			return ((Page) element).getShortName();
		}
		
		return super.getText(element);
	}

}
