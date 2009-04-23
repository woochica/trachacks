function formatItem(row) {
	 return (row[2]) ? row[0] + " <small>(" + row[2] + ")</small>" + "<br/><small>" + row[1] + "</small>" :  row[0] + "<br/><small>" + row[1] + "</small>";
}

