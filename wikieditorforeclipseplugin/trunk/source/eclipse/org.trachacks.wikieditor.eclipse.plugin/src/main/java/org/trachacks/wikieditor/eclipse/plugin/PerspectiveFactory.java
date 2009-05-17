package org.trachacks.wikieditor.eclipse.plugin;

import org.eclipse.ui.IFolderLayout;
import org.eclipse.ui.IPageLayout;
import org.eclipse.ui.IPerspectiveFactory;
import org.trachacks.wikieditor.eclipse.plugin.navigation.NavigationPanel;
import org.trachacks.wikieditor.eclipse.plugin.views.PageHistoryView;

public class PerspectiveFactory implements IPerspectiveFactory {

	public void createInitialLayout(IPageLayout layout) {
		// Get the editor area.
		String editorArea = layout.getEditorArea();

		// Top left: Resource Navigator view
		IFolderLayout left = layout.createFolder("left", IPageLayout.LEFT, 0.25f, editorArea); //$NON-NLS-1$
		left.addView(NavigationPanel.class.getName());

		// Bottom: Page Histoy view
		IFolderLayout bottom = layout.createFolder("bottom", IPageLayout.BOTTOM, 0.85f, editorArea); //$NON-NLS-1$
		bottom.addView(PageHistoryView.class.getName());

		// Top Right: Outline view
		IFolderLayout right = layout.createFolder("right", IPageLayout.RIGHT, 0.75f, editorArea); //$NON-NLS-1$
		right.addView(IPageLayout.ID_OUTLINE);

	}

}
