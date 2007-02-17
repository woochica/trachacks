package mm.eclipse.trac.xmlrpc;

import java.util.Map;

public interface Ticket
{
    
    /**
     * Fetch a ticket.
     * 
     * @param id Ticket id
     * @return [id, time_created, time_changed, attributes]
     */
    Object[] get( int id );
    
    /**
     * Delete ticket with the given id.
     * 
     * @param id
     * @return ??
     */
    int delete( int id );
    
    
    /**
     * Perform a ticket query, returning a list of ticket ID's.
     * 
     * @param query
     * @return an array of ticket ids.
     */
    Object[] query( String query );
    
    /**
     * Create a new ticket, returning the ticket ID.
     * 
     * @param summary Summary of the ticket
     * @param description Ticket Description
     * @param attributes A map containing the ticket attributes
     * @return the newly created ticket id  
     */
    int create( String summary, String description, Map<String,String> attributes );
    
}
