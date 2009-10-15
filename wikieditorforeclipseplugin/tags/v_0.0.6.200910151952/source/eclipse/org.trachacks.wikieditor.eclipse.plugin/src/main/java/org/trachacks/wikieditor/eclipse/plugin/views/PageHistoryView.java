package org.trachacks.wikieditor.eclipse.plugin.views;

import java.text.SimpleDateFormat;

import org.eclipse.jface.viewers.ILabelProviderListener;
import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.ITableLabelProvider;
import org.eclipse.jface.viewers.TableViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Table;
import org.eclipse.swt.widgets.TableColumn;
import org.eclipse.ui.part.IShowInTarget;
import org.eclipse.ui.part.ShowInContext;
import org.eclipse.ui.part.ViewPart;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.views.util.Labels;
import org.trachacks.wikieditor.model.PageInfo;

public class PageHistoryView extends ViewPart implements  IShowInTarget {
	private TableViewer viewer;

	private Page page;

	/**
	 * 
	 * @param page
	 * @see  Viewer#setInput(Object)
	 */
	private void setPage(Page page) {
		if(page == null && this.page != null) {
//			this.page.removeListener(this);
			this.page = null;
		}
		else {
			this.page = page;
//			this.page.addListener(this);
		}
		viewer.setInput(page);
		setContentDescription(Labels.getText("pageHistoryView.description") + page.getDescription()); //$NON-NLS-1$
	}
	
	@Override
	public void createPartControl(Composite parent) {
		Table table = new Table(parent, SWT.MULTI| SWT.H_SCROLL
				| SWT.V_SCROLL | SWT.FULL_SELECTION);
		table.setHeaderVisible(true);
		table.setLinesVisible(true);

		GridData layoutData = new GridData();
		layoutData.grabExcessHorizontalSpace = true;
		layoutData.grabExcessVerticalSpace = true;
		layoutData.horizontalAlignment = GridData.FILL;
		layoutData.verticalAlignment = GridData.FILL;
		table.setLayoutData(layoutData);

		TableColumn column = new TableColumn(table, SWT.LEFT, 0);
		column.setText(Labels.getText("pageHistoryView.version")); //$NON-NLS-1$
		column.setWidth(50);

		column = new TableColumn(table, SWT.LEFT, 1);
		column.setText(Labels.getText("pageHistoryView.date")); //$NON-NLS-1$
		column.setWidth(300);

		column = new TableColumn(table, SWT.LEFT, 2);
		column.setText(Labels.getText("pageHistoryView.author")); //$NON-NLS-1$
		column.setWidth(200);

		column = new TableColumn(table, SWT.LEFT, 3);
		column.setText(Labels.getText("pageHistoryView.comment")); //$NON-NLS-1$
		column.setWidth(300);

		viewer = new TableViewer(table);
		viewer.setContentProvider(new HistoryContentProvider());
		viewer.setLabelProvider(new HistoryLabelProvider());
	}

	@Override
	public void setFocus() {
		viewer.getControl().setFocus();
	}

//	/**
//	 * @see org.trachacks.wikieditor.eclipse.plugin.model.util.IModelChangeListener#tracResourceModified(java.lang.Object)
//	 */
//	public void tracResourceModified(Object page) {
//		if (page == this.page) {
//			viewer.setInput(((Page) page).getPageHistory());
//		}
//	}

	/**
	 *
	 */
	private class HistoryContentProvider implements IStructuredContentProvider {

		public Object[] getElements(Object inputElement) {
			if (inputElement instanceof Page) {
				return ((Page) inputElement).getPageHistory().toArray();
			}
			return null;
		}

		public void dispose() {	
		}

		public void inputChanged(Viewer viewer, Object oldInput, Object newInput) {
		}

	}

	/**
	 * 
	 */
	private class HistoryLabelProvider implements ITableLabelProvider {

		public Image getColumnImage(Object element, int columnIndex) {
			return null;
		}

		public String getColumnText(Object element, int columnIndex) {
			PageInfo version = (PageInfo) element;
			switch (columnIndex) {
			case 0:
				boolean isEditedVersion = page.isEdited() 
						&& version.getVersion().equals(page.getBaseVersion().getVersion());
				return version.getVersion() + (isEditedVersion? "*" : ""); //$NON-NLS-1$ //$NON-NLS-2$
			case 1:
				return (new SimpleDateFormat("yyyy-MM-dd HH:mm"))
						.format(version.getDate());
			case 2:
				return version.getAuthor();
			case 3:
				return version.getComment();

			default:
				return null;
			}
		}

		public void addListener(ILabelProviderListener listener) {
		}

		public void dispose() {
		}

		public boolean isLabelProperty(Object element, String property) {
			return false;
		}

		public void removeListener(ILabelProviderListener listener) {
		}

	}

	/*
	 * (non-Javadoc)
	 * @see org.eclipse.ui.part.IShowInTarget#show(org.eclipse.ui.part.ShowInContext)
	 */
	public boolean show(ShowInContext context) {
		if (viewer != null && context != null) {
			Object input = context.getInput();
			if (input instanceof Page) {
				setPage((Page) input);
				return true;
			}
		}
		return false;
	}

}
