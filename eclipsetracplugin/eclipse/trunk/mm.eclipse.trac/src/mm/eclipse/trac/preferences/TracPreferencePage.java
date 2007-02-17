package mm.eclipse.trac.preferences;

import mm.eclipse.trac.Activator;

import org.eclipse.jface.preference.FieldEditorPreferencePage;
import org.eclipse.jface.preference.StringFieldEditor;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchPreferencePage;

public class TracPreferencePage extends FieldEditorPreferencePage implements
        IWorkbenchPreferencePage
{
    
    public TracPreferencePage()
    {
        super( GRID );
        setPreferenceStore( Activator.getDefault().getPreferenceStore() );
        setDescription( "Trac Plugin Configuration" );
    }
    
    /**
     * Creates the field editors. Field editors are abstractions of the common
     * GUI blocks needed to manipulate various types of preferences. Each field
     * editor knows how to save and restore itself.
     */
    public void createFieldEditors()
    {
        addField( new StringFieldEditor( Preferences.ServerURL, "&Trac URL:",
                getFieldEditorParent() ) );
        
        addField( new StringFieldEditor( Preferences.Username, "&Username:",
                getFieldEditorParent() ) );
        
        StringFieldEditor passwordField = new StringFieldEditor(
                Preferences.Password, "&Password:", getFieldEditorParent() );
        passwordField.getTextControl( getFieldEditorParent() ).setEchoChar(
                (char) 0x2022 );
        addField( passwordField );
    }
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.ui.IWorkbenchPreferencePage#init(org.eclipse.ui.IWorkbench)
     */
    public void init( IWorkbench workbench )
    {}
    
}
