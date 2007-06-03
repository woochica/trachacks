package mm.eclipse.trac.server;

import java.net.MalformedURLException;
import java.net.URL;

import mm.eclipse.trac.Images;
import mm.eclipse.trac.models.TracServer;

import org.eclipse.jface.dialogs.IDialogPage;
import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.events.SelectionListener;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Text;

/**
 * The "New" wizard page allows setting the container for the new file as well
 * as the file name. The page will only accept file name without the extension
 * OR with the extension that matches the expected one (mpe).
 */

public class NewTracServerPage extends WizardPage implements ModifyListener
{
    
    private Text       serverName;
    private Text       serverUrl;
    
    private Button     anonymous;
    private Button     validateButton;
    
    private Text       username;
    private Text       password;
    
    private TracServer server;
    
    public NewTracServerPage()
    {
        super( "wizardPage" );
        setImageDescriptor( Images.getDescriptor( Images.Trac48 ) );
        setTitle( "Add a connection with Trac server" );
        setDescription( "This wizard creates a new connections with a Trac server." );
        setPageComplete( false );
    }
    
    /**
     * @see IDialogPage#createControl(Composite)
     */
    public void createControl( Composite parent )
    {
        Composite container = new Composite( parent, SWT.NULL );
        GridLayout layout = new GridLayout();
        container.setLayout( layout );
        layout.numColumns = 2;
        layout.verticalSpacing = 9;
        
        Label label = new Label( container, SWT.NULL );
        label.setText( "&Server Name" );
        
        serverName = new Text( container, SWT.BORDER | SWT.SINGLE );
        GridData gd = new GridData( GridData.FILL_HORIZONTAL );
        serverName.setLayoutData( gd );
        serverName.addModifyListener( this );
        
        label = new Label( container, SWT.NULL );
        label.setText( "Server &URL" );
        
        serverUrl = new Text( container, SWT.BORDER | SWT.SINGLE );
        gd = new GridData( GridData.FILL_HORIZONTAL );
        serverUrl.setLayoutData( gd );
        serverUrl.addModifyListener( this );
        
        anonymous = new Button( container, SWT.CHECK );
        anonymous.setText( "Connect anonymously" );
        gd = new GridData( GridData.FILL_HORIZONTAL );
        anonymous.setLayoutData( gd );
        anonymous.addSelectionListener( new SelectionListener() {
            public void widgetDefaultSelected( SelectionEvent e )
            {}
            
            public void widgetSelected( SelectionEvent e )
            {
                username.setEnabled( !anonymous.getSelection() );
                password.setEnabled( !anonymous.getSelection() );
                modifyText( null );
            }
        } );
        
        new Label( container, SWT.NULL );
        
        label = new Label( container, SWT.NULL );
        label.setText( "User&name" );
        
        username = new Text( container, SWT.BORDER | SWT.SINGLE );
        gd = new GridData( GridData.FILL_HORIZONTAL );
        username.setLayoutData( gd );
        username.addModifyListener( this );
        
        label = new Label( container, SWT.NULL );
        label.setText( "&Password" );
        
        password = new Text( container, SWT.BORDER | SWT.SINGLE );
        gd = new GridData( GridData.FILL_HORIZONTAL );
        password.setLayoutData( gd );
        password.setEchoChar( (char) 0x2022 );
        password.addModifyListener( this );
        
        validateButton = new Button( container, SWT.PUSH );
        validateButton.setText( "Validate server connection" );
        validateButton.addSelectionListener( new SelectionListener() {

            public void widgetDefaultSelected( SelectionEvent e )
            {
            }

            public void widgetSelected( SelectionEvent e )
            {
                validateConnection();
                if ( isPageComplete() )
                {
                    validateButton.setText( "Connection with server is OK." );
                    validateButton.setEnabled( false );
                }
                else
                {
                    validateButton.setText( "Cannot connect to server." );
                }
            }
            
        } );
        
        setControl( container );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.swt.events.ModifyListener#modifyText(org.eclipse.swt.events.ModifyEvent)
     */
    public void modifyText( ModifyEvent e )
    {
        validateButton.setEnabled( true );
        validateButton.setText( "Validate server connection" );
        
        if ( getServerName().length() == 0 )
        {
            updateStatus( "Please specify a server name" );
            return;
        }
        
        if ( getServerUrl().length() == 0 )
        {
            updateStatus( "Please specify a server URL" );
            return;
        }
        
        URL url;
        try
        {
            url = new URL( getServerUrl() );
            
            if ( !"http".equals( url.getProtocol() )
                    && !"https".equals( url.getProtocol() ) )
            {
                updateStatus( "Invalid protocol scheme '" + url.getProtocol()
                        + "'. Must be 'http' or 'https' " );
                return;
            }
            
            if ( url.getHost().length() == 0 )
            {
                updateStatus( "Invalid hostname" );
                return;
            }
            
        } catch ( MalformedURLException ue )
        {
            updateStatus( "The URL is not valid." );
            return;
        }
        
        setErrorMessage( null );
    }
    
    private void validateConnection()
    {
        // Validate connection
        URL url;
        try
        {
            url = new URL( getServerUrl() );
            
            server = new TracServer( getServerName(), url, getUsername(), getPassword(),
                                     getAnonymous() );
            server.connect();
            if ( !server.isConnected() )
            {
                updateStatus( "Connection with server failed." );
                return;
            }
            
        } catch ( MalformedURLException e )
        {
            updateStatus( "The URL is not valid." );
            return;
        }
        
        setErrorMessage( null );
        setPageComplete( true );
    }
    
    private void updateStatus( String message )
    {
        server = null;
        setErrorMessage( message );
        setPageComplete( false );
    }
    
    public String getServerName()
    {
        return serverName.getText();
    }
    
    public String getServerUrl()
    {
        return serverUrl.getText();
    }
    
    public String getUsername()
    {
        return username.getText();
    }
    
    public String getPassword()
    {
        return password.getText();
    }
    
    public boolean getAnonymous()
    {
        return anonymous.getSelection();
    }
    
    public TracServer getTracServer()
    {
        return server;
    }
}
