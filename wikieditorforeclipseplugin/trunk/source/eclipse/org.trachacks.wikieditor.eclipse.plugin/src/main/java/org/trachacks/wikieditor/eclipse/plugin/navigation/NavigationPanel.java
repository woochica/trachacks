/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation;

import org.eclipse.jface.action.IMenuListener;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.MenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.viewers.DecoratingLabelProvider;
import org.eclipse.jface.viewers.DoubleClickEvent;
import org.eclipse.jface.viewers.IDoubleClickListener;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.jface.viewers.ViewerSorter;
import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Menu;
import org.eclipse.ui.IDecoratorManager;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.navigator.CommonViewer;
import org.eclipse.ui.part.DrillDownAdapter;
import org.eclipse.ui.part.IShowInSource;
import org.eclipse.ui.part.IShowInTarget;
import org.eclipse.ui.part.ShowInContext;
import org.eclipse.ui.part.ViewPart;
import org.trachacks.wikieditor.eclipse.plugin.Activator;
import org.trachacks.wikieditor.eclipse.plugin.editor.WikiPageEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.model.ServerList;
import org.trachacks.wikieditor.eclipse.plugin.model.util.IModelChangeListener;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.PageActionsManager;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.ServerActionsManager;
import org.trachacks.wikieditor.eclipse.plugin.navigation.actions.server.AddServerAction;

/**
 * @author ivan
 *
 */
public class NavigationPanel extends ViewPart implements IModelChangeListener, IDoubleClickListener, IShowInTarget, IShowInSource {

    private CommonViewer viewer;
    private DrillDownAdapter drillDownAdapter;
	private ServerActionsManager serverActionsManager;
	private PageActionsManager pageActionsManager;
	
	/* (non-Javadoc)
	 * @see org.eclipse.ui.part.WorkbenchPart#createPartControl(org.eclipse.swt.widgets.Composite)
	 */
	@Override
    public void createPartControl(Composite parent) {
		viewer = new CommonViewer(this.getClass().getName(), parent, 
				SWT.MULTI | SWT.H_SCROLL | SWT.V_SCROLL);
		viewer.setContentProvider(new TreeContentProvider(this));
		drillDownAdapter = new DrillDownAdapter(viewer);
		
		NavigatorLabelProvider labelProvider = new NavigatorLabelProvider();
		IDecoratorManager manager = Activator.getDefault().getWorkbench().getDecoratorManager();
		viewer.setLabelProvider(new DecoratingLabelProvider(labelProvider,manager));

		viewer.addDoubleClickListener(this);
		viewer.setSorter(new ViewerSorter());
		viewer.setInput(ServerList.getInstance());
		ServerList.getInstance().addListener(this);
		
		
        IToolBarManager toolBarManager = getViewSite().getActionBars().getToolBarManager();
        //IMenuManager menuManager = getViewSite().getActionBars().getMenuManager();
        
        serverActionsManager = new ServerActionsManager(viewer);
        pageActionsManager = new PageActionsManager(viewer);
        
        
        serverActionsManager.fillToolBar(toolBarManager);
        pageActionsManager.fillToolBar(toolBarManager);
        toolBarManager.add(new Separator());
        drillDownAdapter.addNavigationActions(toolBarManager);
        
        
        MenuManager menuMgr = new MenuManager( "#PopupMenu" ); //$NON-NLS-1$
        menuMgr.setRemoveAllWhenShown( true );
        menuMgr.addMenuListener( new IMenuListener() {
            public void menuAboutToShow( IMenuManager manager ) {
                IStructuredSelection selection = (IStructuredSelection) viewer.getSelection();
                if (selection.isEmpty()) {
                    manager.add(new AddServerAction(viewer));
                }
                
                serverActionsManager.fillMenu(manager, selection);
				manager.add(new Separator());
				pageActionsManager.fillMenu(manager, selection);
				manager.add(new Separator(IWorkbenchActionConstants.MB_ADDITIONS));
            }
        } );
        Menu menu = menuMgr.createContextMenu(viewer.getControl());
//        ShowInMenu showInMenu = new ShowInMenu(getSite().getWorkbenchWindow(), "customShowInMenu");
//        showInMenu.fill(menu, 0);
        
		viewer.getControl().setMenu(menu);
		getSite().registerContextMenu(menuMgr, viewer);
	}
    


	/* (non-Javadoc)
	 * @see org.eclipse.ui.part.WorkbenchPart#setFocus()
	 */
	@Override
	public void setFocus() {
		// TODO Auto-generated method stub

	}

	/* (non-Javadoc)
	 * @see org.eclipse.jface.viewers.IDoubleClickListener#doubleClick(org.eclipse.jface.viewers.DoubleClickEvent)
	 */
	public void doubleClick(DoubleClickEvent event) {
		IStructuredSelection selection = (IStructuredSelection) viewer.getSelection();
		serverActionsManager.doubleClick(selection);
		pageActionsManager.doubleClick(selection);
	}

	/**
	 * @see 
	 */
	public void tracResourceModified(Object resource) {
		 try {
			viewer.refresh(resource, true);
		} catch (Exception e) {
			// TODO Fix Exception when 'viewer is disposed' 
			e.printStackTrace();
		}
	}

	/*
	 * (non-Javadoc)
	 * @see org.eclipse.ui.part.IShowInTarget#show(org.eclipse.ui.part.ShowInContext)
	 */
	public boolean show(ShowInContext context) {
		if (viewer != null && context != null) {
			Object input = context.getInput();
			if (input instanceof WikiPageEditorInput) {
				viewer.setSelection(new StructuredSelection(((WikiPageEditorInput) input).getWikiPage()));
				return true;
			}
		}
		return false;
	}

	/*
	 * (non-Javadoc)
	 * @see org.eclipse.ui.part.IShowInSource#getShowInContext()
	 */
	public ShowInContext getShowInContext() {
		Object input = ((IStructuredSelection) viewer.getSelection()).getFirstElement();
		return new ShowInContext(input, viewer.getSelection());
	}

}
