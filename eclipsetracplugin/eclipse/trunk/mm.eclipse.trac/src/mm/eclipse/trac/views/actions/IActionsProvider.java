package mm.eclipse.trac.views.actions;

import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.viewers.IStructuredSelection;

public interface IActionsProvider
{   
    void fillMenu( IMenuManager menu, IStructuredSelection selection );
}
