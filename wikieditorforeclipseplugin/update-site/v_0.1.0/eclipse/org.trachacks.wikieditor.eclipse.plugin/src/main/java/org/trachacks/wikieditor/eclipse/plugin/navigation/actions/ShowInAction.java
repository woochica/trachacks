/*******************************************************************************
 * Copyright (c) 2000, 2006 IBM Corporation and others.
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v10.html
 *
 * Contributors:
 *     IBM Corporation - initial API and implementation
 *******************************************************************************/

package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.eclipse.ui.IViewPart;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.part.IShowInTarget;
import org.eclipse.ui.part.ShowInContext;
import org.trachacks.wikieditor.eclipse.plugin.model.AbstractBaseObject;

/**
 * Action for a particular target in the Show In menu.
 */
public class ShowInAction extends AbstractBaseAction {

	private StructuredViewer viewer;
	private String targetViewId;
	public ShowInAction(StructuredViewer viewer, String targetViewId) {
		super();
		this.viewer = viewer;
		this.targetViewId = targetViewId;
	}
	
	/**
	 * 
	 */
	@Override
	public void runInternal() throws Exception {

		IViewPart viewPart = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage()
				.showView(targetViewId);

		if (viewPart instanceof IShowInTarget) {
			IShowInTarget target = (IShowInTarget) viewPart;
			Object selectedObject = getSingleSelection(viewer, AbstractBaseObject.class);
			if(selectedObject != null) {
				ShowInContext showInContext = new ShowInContext(selectedObject, new StructuredSelection(selectedObject));
				target.show(showInContext);
				return;
			}
		}
	}

}
