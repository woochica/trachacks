/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation;

import org.eclipse.jface.viewers.IDecoration;
import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.ILightweightLabelDecorator;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 * 
 */
public class NavigatorLabelDecorator implements ILightweightLabelDecorator {

	/**
	 * @see org.eclipse.jface.viewers.ILightweightLabelDecorator#decorate(java.lang.Object,
	 *      org.eclipse.jface.viewers.IDecoration)
	 */
	public void decorate(Object element, IDecoration decoration) {
		if (element instanceof Page) {
			Page page = (Page) element;
			if(page.isBrandNew()) {
				decoration.addOverlay(Images.getDescriptor(Images.PAGE_NEW_OVERLAY), IDecoration.BOTTOM_LEFT);
			}
			else if(page.wasDeleted()) {
				decoration.addOverlay(Images.getDescriptor(Images.PAGE_REMOVED_OVERLAY), IDecoration.BOTTOM_LEFT);
			}
			else if(page.isEditedConcurrently()) {
				decoration.addOverlay(Images.getDescriptor(Images.PAGE_EDIT_CONFLICT_OVERLAY), IDecoration.BOTTOM_LEFT);
			}
			else if (page.isEdited()) {
				decoration.addOverlay(Images.getDescriptor(Images.PAGE_MODIFIED_OVERLAY), IDecoration.BOTTOM_LEFT);
			}
		}
	}

	/**
	 * @see org.eclipse.jface.viewers.IBaseLabelProvider#addListener(org.eclipse.jface.viewers.ILabelProviderListener)
	 */
	public void addListener(ILabelProviderListener arg0) {
	}

	/**
	 * @see org.eclipse.jface.viewers.IBaseLabelProvider#dispose()
	 */
	public void dispose() {
	}

	/**
	 * @see org.eclipse.jface.viewers.IBaseLabelProvider#isLabelProperty(java.lang.Object, java.lang.String)
	 */
	public boolean isLabelProperty(Object arg0, String arg1) {
		return false;
	}

	/**
	 * @see org.eclipse.jface.viewers.IBaseLabelProvider#removeListener(org.eclipse.jface.viewers.ILabelProviderListener)
	 */
	public void removeListener(ILabelProviderListener arg0) {
	}

}
