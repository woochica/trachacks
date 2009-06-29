/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation.actions;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredViewer;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.AddSubPageAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.CommitPageAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.DeletePageAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.DeletePageVersionAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.MarkAsMergedAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.MergePageAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.OpenPageEditorAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.RefreshSelectionAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.ShowPageHistoryAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.ShowPagePropertiesAction;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.page.UneditPageAction;
import org.trachacks.wikieditor.eclipse.plugin.views.PageHistoryView;

/**
 * @author ivan
 *
 */
public class PageActionsManager {

    private StructuredViewer viewer;
    
    private Action openEditor;
    private Action refresh;
    private Action addSubPage;
    private Action unedit;
    private Action commit;
    private Action merge;
    private Action markAsMerged;
    private Action showHistory;
    private Action delete;
    private Action deleteVersion;
    private Action showProperties;
	
	public PageActionsManager(StructuredViewer viewer) {
		super();
		this.viewer = viewer;
		openEditor = new OpenPageEditorAction(viewer);
		refresh = new RefreshSelectionAction(viewer);
		addSubPage = new AddSubPageAction(viewer);
		unedit = new UneditPageAction(viewer);
		commit = new CommitPageAction(viewer);
		merge = new MergePageAction(viewer);
		markAsMerged = new MarkAsMergedAction(viewer);
		showHistory = new ShowPageHistoryAction(viewer, PageHistoryView.class.getName());
		delete = new DeletePageAction(viewer);
		deleteVersion = new DeletePageVersionAction(viewer);
		showProperties = new ShowPagePropertiesAction(viewer);
	}
    
	public void fillMenu(IMenuManager menu, IStructuredSelection selection) {
		if (selection.size() == 1 && selection.getFirstElement() instanceof Page) {
			Page page = (Page) selection.getFirstElement();

			boolean hasRemotePage = !page.isBrandNew() && ! page.isFolder(); 
			
			menu.add(openEditor);
			menu.add(refresh);
			menu.add(new Separator());
			menu.add(addSubPage);
			menu.add(new Separator());
			menu.add(commit);
			commit.setEnabled(page.isEdited() && !page.isEditedConcurrently());
			menu.add(unedit);
			unedit.setEnabled(page.isEdited());
			menu.add(merge);
			merge.setEnabled(page.isEditedConcurrently());
			menu.add(markAsMerged);
			markAsMerged.setEnabled(page.isEditedConcurrently());
			menu.add(new Separator());
			if(hasRemotePage) {
				menu.add(delete);
				menu.add(deleteVersion);
				menu.add(new Separator());
			}
			menu.add(showHistory);
			menu.add(showProperties);
		}
	}
	public void fillToolBar(IToolBarManager toolBarManager) {
		
	}
	
	 public void doubleClick(IStructuredSelection selection) {
			if (selection.size() == 1 && selection.getFirstElement() instanceof Page) {
				Page page = (Page) selection.getFirstElement();
				if(page.isEditedConcurrently()) {
					merge.run();
				}
				else {
					openEditor.run();
				}
			}		 
	 }
}
