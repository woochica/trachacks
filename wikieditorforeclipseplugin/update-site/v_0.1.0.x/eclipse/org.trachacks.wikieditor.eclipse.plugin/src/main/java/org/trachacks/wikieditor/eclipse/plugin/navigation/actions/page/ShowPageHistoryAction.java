/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.ShowInAction;

/**
 * @author ivan
 *
 */
public class ShowPageHistoryAction extends ShowInAction {

	public ShowPageHistoryAction(StructuredViewer viewer, String targetViewId) {
		super(viewer,  targetViewId);
		setText("Show Page History");
		setImageDescriptor(Images.getDescriptor(Images.TRAC_16));
	}

}
