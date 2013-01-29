/**
 * Get a list of all TR nodes in the table which are not currently visible
 * (useful for building forms).
 *  @name fnGetHiddenNodes
 *  @anchor fnGetHiddenNodes
 *  @author <a href="http://sprymedia.co.uk">Allan Jardine</a>
 */

 $.fn.dataTableExt.oApi.fnGetCheckedNodes = function ( oSettings )
 {
    /* Note the use of a DataTables 'private' function thought the 'oApi' object */
    var anNodes = this.oApi._fnGetTrNodes( oSettings );
    return anNodes;
 };
 function fnGetNodeValues(data)
 {
    var ret = new Array();
    for ( var i=0 ; i<data.length ; i++ )
    {
      ret[i] = data[i].value;
    }
    return ret.join();
 };
