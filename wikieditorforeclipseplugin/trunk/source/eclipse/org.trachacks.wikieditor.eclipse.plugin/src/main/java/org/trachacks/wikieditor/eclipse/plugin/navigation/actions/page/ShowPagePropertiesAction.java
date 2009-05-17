/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;

/**
 * @author ivan
 *
 */
public class ShowPagePropertiesAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public ShowPagePropertiesAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Properties");
		//setImageDescriptor(Images.getDescriptor(Images.ERROR)); // XXX
	}
	
	@Override
	public void runInternal() {
		// TODO Auto-generated method stub
		
	}
	
}
