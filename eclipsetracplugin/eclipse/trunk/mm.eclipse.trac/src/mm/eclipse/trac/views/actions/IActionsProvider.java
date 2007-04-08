package mm.eclipse.trac.views.actions;

import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.viewers.IStructuredSelection;

/**
 * Interface for action providers.
 * 
 * 
 * @author Matteo Merli <matteo.merli@gmail.com>
 * 
 */
public interface IActionsProvider
{
    /**
     * Fill in a context menu based on the current element(s) selected.
     * 
     * @param menu
     *            a menu object to fill
     * @param selection
     *            the current selection
     */
    void fillMenu( IMenuManager menu, IStructuredSelection selection );
    
    /**
     * Run actions based on element(s) selected on a double-click event.
     * 
     * @param selection
     *            the current selection
     */
    void doubleClick( IStructuredSelection selection );
}
