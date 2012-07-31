var wikitoolbartpl_description = new Array();
var wikitoolbartpl_text = new Array();

wikitoolbartpl_description["listtags"] = "List Items With Tag(s)";
wikitoolbartpl_text["listtags"] = "[[ListTagged(expression=\"<TAG EXPRESSION>\")]]\n";

wikitoolbartpl_description["listtickets_openbug"] = "List Open Bug Tickets";
wikitoolbartpl_text["listtickets_openbug"] = "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status!=closed&type!=Feature)]]\n";

wikitoolbartpl_description["listtickets_closedbug"] = "List Closed Bug Tickets";
wikitoolbartpl_text["listtickets_closedbug"] = "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status!=closed&type!=Feature)]]\n";

wikitoolbartpl_description["listtickets_openfeature"] = "List Open Feature Tickets";
wikitoolbartpl_text["listtickets_openfeature"] = "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status!=closed&type=Feature)]]\n";

wikitoolbartpl_description["listtickets_closedfeature"] = "List Closed Feature Tickets";
wikitoolbartpl_text["listtickets_closedfeature"] = "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status=closed&type=Feature)]]\n";

wikitoolbartpl_description["link_milestone"] = "Link Milestone";
wikitoolbartpl_text["link_milestone"] = "[milestone:\"<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>\"]\n";

wikitoolbartpl_description["link_changelists"] = "Link Changelists";
wikitoolbartpl_text["link_changelists"] = "[log:<PRODUCT DEPOT MAIN DIR: USE //depot/blabla>@<FROM CHANGELIST>:<TO CHANGELIST>]\n";

wikitoolbartpl_description["link_source"] = "Link Source Directory Or File";
wikitoolbartpl_text["link_source"] = "[source:<PRODUCT DEPOT DIR OR FILE: USE //depot/blabla/bla.c>]\n";

wikitoolbartpl_description["link_uncpath"] = "Link UNC Path";
wikitoolbartpl_text["link_uncpath"] = "[file:////\\\\<UNC PATH> <UNC PATH>]\n";

wikitoolbartpl_description["format_newsflash"] = "NewsFlash";
wikitoolbartpl_text["format_newsflash"] = "[[NewsFlashStart]]\n<NEWS FLASH TEXT>\n[[NewsFlashEnd]]\n";

wikitoolbartpl_description["tpl_milestone"] = "Milestone Template";
wikitoolbartpl_text["tpl_milestone"] = 
  "Version <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION> of <PRODUCT FULLNAME>.\n"
+ "\n"
+ "== Bugs solved ==\n"
+ "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status=closed&type!=Feature)]]\n"
+ "\n"
+ "== New features ==\n"
+ "[[TicketQuery(milestone=<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>&status=closed&type=Feature)]]\n"
+ "\n"
+ "== Related issues ==\n"
+ "[[ListTagged(expression=\"<PRODUCT TAG>+<VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>\")]]\n"
+ "\n"
+ "== Changelist ==\n"
+ "[log:<PRODUCT DEPOT MAIN DIR: USE //depot/blabla>@<FROM CHANGELIST>:<TO CHANGELIST>]\n"
+ "\n";

wikitoolbartpl_description["tpl_productentry"] = "Product Entry Template";
wikitoolbartpl_text["tpl_productentry"] = 
" * [wiki:MyProduct My Product] ([source://depot/ Browse Source])"
+ "\n";

wikitoolbartpl_description["tpl_productmainpage"] = "Product Main Page Template";
wikitoolbartpl_text["tpl_productmainpage"] = 
  "= <PRODUCT FULLNAME> =\n"
+ "\n"
+ "<SHORT DESCRIPTION>\n"
+ "\n"
+ "== Latest ==\n"
+ "\n"
+ "||'''Release'''||'''Pre-Release'''||\n"
+ "||[milestone:\"<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>\"]||[milestone:\"<PRODUCT TAG> <VERSION MAJOR>.<VERSION MINOR>.<VERSION REVISION>\"]||\n"
+ "\n"
+ "== Documentation ==\n"
+ "\n"
+ " * [file:////\\\\Rdw2kserver\\Doc&Opl\\ebooks\\ <PRODUCT FULLNAME> Documentation]\n"
+ " * [file:////\\Rdw2kserver\\Public\\Products\\ <PRODUCT FULLNAME> Release Notes]\n"
+ "\n"
+ "== Knowledge Base ==\n"
+ "\n"
+ "[[ListTagged(expression=\"KB+<PRODUCT TAG>\")]]\n"
+ "\n"
+ "== Issues ==\n"
+ "\n"
+ "=== Open Bugs ===\n"
+ "\n"
+ "[[TicketQuery(version^=<PRODUCT TAG>&status!=closed&type!=Feature)]]\n"
+ "\n"
+ "=== Open Features ===\n"
+ "\n"
+ "[[TicketQuery(version^=<PRODUCT TAG>&status!=closed&type=Feature)]]\n"
+ "\n";

//DO NOT REMOVE THIS!
addWikiToolbar(WikiTemplatesToolbar);
