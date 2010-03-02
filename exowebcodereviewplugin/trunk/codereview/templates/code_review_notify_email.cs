<html><head><title><?cs var:trac_name ?> Trac ChangeSet <?cs var:cs_id ?> has been reviewed.</title>
<style type="text/css">
<!--
    
    /* h1, h2, h3, h4, h5, h6 style*/
    h1 { font-size: 16px; }
    h2 { font-size: 15px; }
    h3 { font-size: 14px; }
    h4 { font-size: 13px; }
    h5 { font-size: 12px; text-transform: uppercase; }
    h6 { font-size: 11px; text-transform: uppercase; }

    /* link style */
    :link {
        text-decoration: none;
        color: #b00;
        border-bottom: 1px dotted #bbb;
    }


    /* code style */
    div.code{
        background: #f7f7f7;
        border: 1px solid #d7d7d7;
        margin: 1em 1.75em;
        padding: .25em;
        overflow: auto;
        font-size: 15px;
        position: relative;
    }
       
    div.code pre { margin: 0; }
   
    table.code {
        border: 1px solid #ddd;
        border-spacing: 0;
        border-top: 0;
        empty-cells: show;
        font-size: 12px;
        line-height: 130%;
        padding: 0;
        margin: 0 auto;
        table-layout: fixed;
        width: 100%;
    }
    table.code th {
        border-right: 1px solid #d7d7d7;
        border-bottom: 1px solid #998;
        font-size: 11px;
    }
    table.code th.lineno { width: 4em }
    table.code thead th {
        background: #eee;
        border-top: 1px solid #d7d7d7;
        color: #999;
        padding: 0 .25em;
        text-align: center;
        white-space: nowrap;
    }
    table.code tbody th {
        background: #eed;
        color: #886;
        font-weight: normal;
        padding: 0 .5em;
        text-align: right;
        vertical-align: top;
    }
    table.code tbody th :link, table.code tbody th :visited {
        border: none;
        color: #886;
        text-decoration: none;
    }
    table.code tbody th :link:hover, table.code tbody th :visited:hover {
        color: #000;
    }

    table.code tbody td {
        background: #fff;
        font: normal 11px monospace;
        overflow: hidden;
        padding: 1px 2px;
        vertical-align: top;
    }

    .image-file { background: #eee; padding: .3em }
    .image-file img { background: url(../imggrid.png) }

    /* Default */
    .code-block span {
        font-family: monospace;
    }

    /* Comments */
    .code-comment, .css_comment, .c_comment, .c_commentdoc, .c_commentline,
    .c_commentlinedoc, .h_comment,.pl_commentline, .p_commentblock,
    .hphp_comment, .hphp_commentblock, .hphp_commentline,
    .yaml_comment {
        color: #f93;
        font-style: italic;
    }
    .p_commentline {
        font-style: normal;
        font-size: 11px;
        font-family: Arial;
        color: #999;
        display: block:
        margin: 0;
        padding: 0;
        position: absolute;
        top: -1px;
        right: 2px;
    }
    
    /* Language keyword */
    .code-keyword, .pl_word  { color: #789; font-weight: bold }
    
    /* Type */
    .code-type, .c_word, .c_word2, .p_classname, .hphp_classname{
        color: #468;
        font-weight: bold;
    }
    
    /* Function */
    .code-func, .p_defname{
        color: #900;
        font-weight: bold;
        border-bottom: none;
    }
    
    /* Pre-processor */
    .code-prep, .c_preprocessor, .pl_preprocessor, .yaml_identifier {
        color: #999;
        font-weight: bold;
    }
    
    /* Language construct */
    .code-lang, .p_word { color: #000; font-weight: bold }
    
    /* String */
    .code-string, .c_string, .c_stringeol, .css_doublestring, .css_singlestring,
    .h_singlestring, .h_doublestring, .pl_string, .pl_string_q, .pl_string_qq,
    .pl_string_qr, .pl_string_qw, .pl_string_qx, .pl_backticks, .pl_character,
    .p_string, .p_stringeol, .hphp_string, .hphp_stringeol, .hphp_triple,
    .hphp_tripledouble, .p_character, .p_triple, .p_tripledouble {
        color: #f6c;
        font-weight: normal;
    }
    
    /* Variable name */
    .code-var { color: #f9f }


    /* SilverCity-specific styles */
    .css_id, .css_class, .css_pseudoclass, .css_tag { color: #900000 }
    .css_directive { color: #009000; font-weight: bold }
    .css_important { color: blue }
    .css_operator { color: #000090; font-weight: bold }
    .css_tag { font-weight: bold }
    .css_unknown_identifier, .css_unknown_pseudoclass { color: red }
    .css_value { color: navy }
    .c_commentdockeyword { color: navy; font-weight: bold }
    .c_commentdockeyworderror { color: red; font-weight: bold }
    .c_character, .c_regex, .c_uuid, .c_verbatim { color: olive }
    .c_number { color: #099 }
    .h_asp { color: #ff0 }
    .h_aspat { color: #ffdf00 }
    .h_attribute { color: teal }
    .h_attributeunknown { color: red }
    .h_cdata { color: #373 }
    .h_entity { color: purple }
    .h_number { color: #099 }
    .h_other { color: purple }
    .h_script, .h_tag, .h_tagend { color: navy }
    .h_tagunknown { color: red }
    .h_xmlend, .h_xmlstart { color: blue }
    .pl_datasection { color: olive }
    .pl_error { color: red; font-weight: bold }
    .pl_hash { color: #000 }
    .pl_here_delim, .pl_here_q, .pl_here_qq, .pl_here_qx, .pl_longquote { color: olive }
    .pl_number { color: #099 }
    .pl_pod { font-style: italic }
    .pl_regex, .pl_regsubst { color: olive }
    .p_number { color: #099 }
    .hphp_character { color: olive }
    .hphp_defname { color: #099; font-weight: bold }
    .hphp_number { color: #099 }
    .hphp_word { color: navy; font-weight: bold }
    .yaml_document { color: gray; font-style: italic }
    .yaml_keyword { color: #808 }
    .yaml_number { color: #800 }
    .yaml_reference { color: #088 }
    .v_comment { color: gray; font-style: italic }
    .v_commentline, .v_commentlinebang { color: red; font-style: italic }
    .v_number, .v_preprocessor { color: #099 }
    .v_string, .v_stringeol { color: olive }
    .v_user{ color: blue; font-weight: bold }
    .v_word, .v_word3 { color: navy; font-weight: bold }
    .v_word2 { color: green; font-weight: bold }

-->
</style>
</head>
<body style="background: #fff; color: #000; margin: 10px; padding: 0; font: normal 13px;">
<div style="float: left; width: 40%; margin-bottom: 8px;">
    <strong>
      <a href="<?cs var:absurl ?>/changeset/<?cs var:cs_id ?>"
        style="color: #b00; text-decoration:none; border-bottom: 1px, dotted #bbb">Changeset r<?cs var:cs_id ?></a>
    </strong> by <?cs var:cs_author ?><br>
    <strong>
      <a href="<?cs var:absurl ?>/CodeReview/<?cs var:cs_id ?>"
        style="color: #b00; text-decoration:none; border-bottom: 1px, dotted #bbb">Reviewed</a>
    </strong> by <?cs var:r_author ?><br>
    <?cs if:r_priority != "normal"?>
        <strong>Priority:</strong> <?cs var:r_priority ?><br>
    <?cs /if ?>
    <?cs if:ticket_len != 0 ?>
      <strong>Referenced tickets:</strong><br>
      <?cs each:item=t_info ?>
        <a href="<?cs var:absurl ?>/ticket/<?cs var:item.id?>"
           style="color: #b00; text-decoration:none; border-bottom: 1px, dotted #bbb">#<?cs var:item.id ?></a> (<?cs var:item.summary ?>)<br>
      <?cs /each ?>
    <?cs /if ?>
</div>

<div style="float: right; width: 60%;  background-color: #eee; margin: 0; margin-bottom: 8px;">
    <h2  style="font-size: 12px; font-weight: bold; text-transform: uppercase; padding: 2px; margin: 0; color: #aaa; background-color: #eee; display: block">COMMIT MESSAGE</h2>
    <?cs var:cs_message ?>
</div>

<div style="clear: both; border: solid #eee 2px;">
    <h2  style="font-size: 12px; font-weight: bold; text-transform: uppercase; padding: 2px; margin: 0; color: #aaa; background-color: #eee; display: block">CODE REVIEW COMMENTS</h2>
    <?cs var:r_content ?>
</div>

<!--
<div style="clear: both; border: solid #eee 2px;">
    <h2  style="font-size: 12px; font-weight: bold; text-transform: uppercase; padding: 2px; margin: 0; color: #aaa; background-color: #eee; display: block">Welcome to use BamWho!</h2>
<p>BAM Who is a micro-blogging type of service similar to twitter and jaiku.</p>
<p>If you want to have a try, you could use the following way:</p>
<ul>
  <li>Add bamboo@exoweb.net as your friend by msn, jabber or gtalk clients.</li>
  <li>Send "sign-up" to bamboo@exoweb.net. And you could send it "help" to get more details.</li>
</ul>
<p>If you have some problems, please send your questions and comments to &lt;<a href="mailto:research@exoweb.net">research@exoweb.net</a>&gt;</p>
<p>Thanks</p>
</div>
-->

</body>
</html>
