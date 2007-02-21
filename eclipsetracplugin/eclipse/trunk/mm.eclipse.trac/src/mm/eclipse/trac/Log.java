package mm.eclipse.trac;

import org.eclipse.core.runtime.Status;

public class Log
{
    public static void error( String message )
    {
        error( message, null );
    }
    
    public static void error( String message, Exception e )
    {
        log( Status.ERROR, message, e );
    }
    
    public static void warning( String message )
    {
        warning( message, null );
    }
    
    public static void warning( String message, Exception e )
    {
        log( Status.WARNING, message, e );
    }
    
    public static void info( String message )
    {
        log( Status.INFO, message, null );
    }
    
    private static void log( int level, String message, Exception e )
    {
        Activator.getDefault().getLog().log(
                                             new Status( level, Activator.PLUGIN_ID,
                                                         Status.OK, message, e ) );
    }
}
