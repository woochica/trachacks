/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page;

import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.swt.SWT;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.AbstractBaseAction;

/**
 * @author ivan
 *
 */
public class RefreshSelectionAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	/**
	 * 
	 */
	public RefreshSelectionAction(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		setText("Refresh");
		setImageDescriptor(Images.getDescriptor(Images.REFRESH));
		setAccelerator(SWT.F5);
	}

	@Override
	public void runInternal() {
		Page page = getSingleSelection(viewer, Page.class);
		if(page != null) {
			page.refresh();
		}
	}
}
