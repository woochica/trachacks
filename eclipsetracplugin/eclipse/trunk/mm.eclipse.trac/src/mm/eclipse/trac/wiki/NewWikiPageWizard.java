package mm.eclipse.trac.wiki;

import mm.eclipse.trac.Images;
import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.TracServer;
import mm.eclipse.trac.models.TracServerList;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Combo;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Text;

public class NewWikiPageWizard extends WizardPage implements ModifyListener
{
    private Combo      serverName;
    
    private Text       pageName;
    
    private TracServer tracServer;
    private WikiPage   parentPage;
    
    public NewWikiPageWizard( TracServer tracServer, WikiPage parentPage )
    {
        super( "wizardPage" );
        setImageDescriptor( Images.getDescriptor( Images.Trac48 ) );
        setTitle( "Add a new Wiki page" );
        setDescription( "This wizard creates a new page in the Trac wiki." );
        this.tracServer = tracServer;
        this.parentPage = parentPage;
        setPageComplete( false );
    }
    
    public void createControl( Composite parent )
    {
        Composite container = new Composite( parent, SWT.NULL );
        GridLayout layout = new GridLayout();
        container.setLayout( layout );
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
        
        Label label = new Label( container, SWT.NULL );
        label.setText( "&Server Name" );
        
        serverName = new Combo( container, SWT.DROP_DOWN | SWT.READ_ONLY );
        GridData gd = new GridData( GridData.FILL_HORIZONTAL );
        serverName.setLayoutData( gd );
        int idx = 0;
        
        for ( TracServer server : TracServerList.getInstance() )
        {
            if ( server.isConnected() )
            {
                serverName.add( server.getName() );
                
                if ( server == tracServer )
                {
                    serverName.select( idx );
                }
                ++idx;
            }
        }
        serverName.addModifyListener( this );
        
        label = new Label( container, SWT.NULL );
        label.setText( "Page &Name: " );
        
        pageName = new Text( container, SWT.BORDER | SWT.SINGLE );
        gd = new GridData( GridData.FILL_HORIZONTAL );
        pageName.setLayoutData( gd );
        pageName.addModifyListener( this );
        if ( parentPage != null )
            pageName.setText( parentPage.getFullName() + "/" );
        
        setControl( container );
    }
    
    public void modifyText( ModifyEvent event )
    {
        Log.info( "Server name: " + serverName.getText() );
        TracServer s = TracServerList.getInstance()
                .getServerByName( serverName.getText() );
        if ( s == null )
        {
            updateStatus( "Invalid server selected." );
            return;
        }
        
        if ( pageName.getText().length() == 0 )
        {
            updateStatus( "Please specify a page name." );
            return;
        }
        
        if ( pageName.getText().endsWith( "/" ) )
        {
            updateStatus( "Page name cannot ends with a trailing '/'" );
            return;
        }
        
        try
        {
            s.getWiki().getPage( pageName.getText() );
            
            updateStatus( "Page '" + pageName.getText() + "' already exists." );
            return;
        } catch ( Exception ex )
        {
            // Ok page does not exists, we can create it
        }
        
        setErrorMessage( null );
        setPageComplete( true );
    }
    
    private void updateStatus( String message )
    {
        setErrorMessage( message );
        setPageComplete( false );
    }
    
    public String getServerName()
    {
        return serverName.getText();
    }
    
    public String getPageName()
    {
        return pageName.getText();
    }
    
}
