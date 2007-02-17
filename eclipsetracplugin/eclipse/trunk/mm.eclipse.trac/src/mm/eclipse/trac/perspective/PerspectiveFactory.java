package mm.eclipse.trac.perspective;

import org.eclipse.ui.IFolderLayout;
import org.eclipse.ui.IPageLayout;
import org.eclipse.ui.IPerspectiveFactory;

public class PerspectiveFactory implements IPerspectiveFactory
{
    
    public void createInitialLayout( IPageLayout layout )
    {
        // Get the editor area.
        String editorArea = layout.getEditorArea();
        
        // Top left: Resource Navigator view
        IFolderLayout left = layout.createFolder( "left", IPageLayout.LEFT, 0.25f,
                                                  editorArea );
        left.addView( "mm.eclipse.trac.views.TracNavigator" );
        
        // Bottom: Page Histoy view
        IFolderLayout bottom = layout.createFolder( "bottom", IPageLayout.BOTTOM, 0.85f,
                                                    editorArea );
        bottom.addView( "mm.eclipse.trac.views.WikiPageHistory" );
        
        // Top Right: Outline view
        IFolderLayout right = layout.createFolder( "right", IPageLayout.RIGHT, 0.75f,
                                                   editorArea );
        right.addView( IPageLayout.ID_OUTLINE );
        
    }
    
}
