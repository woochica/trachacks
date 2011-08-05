package org.trachacks.wikieditor.eclipse.plugin;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.resource.ImageRegistry;
import org.eclipse.swt.graphics.Image;
import org.eclipse.ui.PlatformUI;

public enum Images {
    
    ERROR("error.gif"), 
    REFRESH("refresh.gif"),
    FOLDER("folder.gif"),
    LINK_WITH_EDITOR("link_with_editor.gif"),
    
    ADD_NEW_SERVER("add_server.png"),
    SERVER_CONNECTED("server_connected.png"), 
    SERVER_DISCONNECTED("server_disconnected.png"),
    DELETE_SERVER("delete_obj.gif"),
    
    ADD_NEW_PAGE("add_page.png"),
    UNEDIT_PAGE("undo.gif"),
    COMMIT_PAGE("commit_page.gif"),
    FORCE_COMMIT_PAGE("force_commit_page.gif"),
    DELETE_PAGE("delete_obj.gif"),

    PAGE_MODIFIED_OVERLAY("decorators/page_modified.png"),
    PAGE_EDIT_CONFLICT_OVERLAY("decorators/page_edit_conflict.gif"),
    PAGE_NEW_OVERLAY("decorators/page_new.gif"),
    PAGE_REMOVED_OVERLAY("decorators/page_removed_ov.gif"),

    REQUIRED_FIELD_OVERLAY("decorators/required_field.gif"),
    INVALID_FIELD_OVERLAY("decorators/invalid_field.gif"),
    
    MACRO("editor/macro.gif"), 
    WORD("editor/word.png"),
    TEMPLATE("editor/template.gif"),
    STEP("editor/step.gif"),


    TRAC_16("trac_16.png"),
    TRAC_48("trac_48.png");
    
    ////////////////////////////////////////////////////
    
    private final String path;

	private Images(String filename) {
		this.path = "icons/" + filename;
	}

	public String getPath() {
		return path;
	}

	/**
	 * 
	 * 
	 * @param img
	 *            The image enumeration reference
	 * @return The image instance
	 */
	public static Image get(Images img) {
		ImageRegistry registry = Activator.getDefault().getImageRegistry();
		Image image = registry.get(img.path);
		if (image == null) {
			ImageDescriptor desc = Activator.getImageDescriptor(img.path);
			registry.put(img.path, desc);
			image = registry.get(img.path);
		}
		return image;
	}

	public static ImageDescriptor getDescriptor(Images img) {
		ImageRegistry registry = Activator.getDefault().getImageRegistry();
		ImageDescriptor descriptor = registry.getDescriptor(img.path);
		if (descriptor == null) {
			descriptor = Activator.getImageDescriptor(img.path);
			registry.put(img.path, descriptor);
		}
		return descriptor;
	}

	public static ImageDescriptor getShared(String img) {
		return PlatformUI.getWorkbench().getSharedImages().getImageDescriptor(
				img);
	}

}
