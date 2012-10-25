trac-admin e:\Trac\Projects\%1 initenv --inherit=E:\Trac\Template\conf\trac.ini
trac-admin e:\Trac\Projects\%1 permission add lloyd.fernandes TRAC_ADMIN
trac-admin e:\Trac\Projects\%1 permission add amaresh.misra TRAC_ADMIN
trac-admin e:\Trac\Projects\%1 permission remove anonymous *
trac-admin e:\Trac\Projects\%1 permission add authenticated BROWSER_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated CHANGESET_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated FILE_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated LOG_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated MILESTONE_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated REPORT_SQL_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated REPORT_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated ROADMAP_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated SEARCH_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated TICKET_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated TIMELINE_VIEW
trac-admin e:\Trac\Projects\%1 permission add authenticated WIKI_VIEW
trac-admin e:\Trac\Projects\%1 wiki remove *
