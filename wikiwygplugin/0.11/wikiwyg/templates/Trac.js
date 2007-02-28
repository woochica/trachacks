//------------------------------------------------------------------------------
// onload should wikify the html. search for a better possibility
//
addEvent("onload", (
  function() {
    var div = $(".wikipage")[0];  // uses JQuery
    Wikiwyg.Trac.setup_wikiwyg_section(div, '${href()}/chrome/');  //should be something like '/my-env/chrome/'
  })
);


//------------------------------------------------------------------------------
proto = new Subclass('Wikiwyg.Trac', 'Wikiwyg');
klass = Wikiwyg.Trac;

klass.setup_wikiwyg_section = function(wiki, proj_href) {
  var myWikiwyg = new Wikiwyg.Trac();
  var myConfig = {
    toolbar: {imagesLocation: proj_href+'wikiwyg/'},
    doubleClickToEdit: true,
    projectHref: proj_href
  }
  myWikiwyg.createWikiwygArea(wiki, myConfig);
  return true;
}

proto.modeClasses = [
    'Wikiwyg.Wysiwyg',
    'Wikiwyg.Wikitext.Trac',
    'Wikiwyg.Preview'
];

proto.saveChanges = function() {
  alert('implement save');
}

//------------------------------------------------------------------------------
// proto = new Subclass('Wikiwyg.Toolbar.Trac', 'Wikiwyg.Toolbar');
// extend if you want a special toolbar

//------------------------------------------------------------------------------
proto = new Subclass('Wikiwyg.Wikitext.Trac', 'Wikiwyg.Wikitext');

proto.config = {
    textareaId: null,
    supportCamelCaseLinks: true,
    javascriptLocation: null,
    clearRegex: null,
    editHeightMinimum: 10,
    editHeightAdjustment: 1.3,
    markupRules: {
        link: ['bound_phrase', '[', ']'],
        bold: ['bound_phrase', "'''", "'''"],
        italic: ['bound_phrase', "''", "''"],
        p: ['start_lines', ''],
        pre: ['bound_phrase', '{{{', '}}}'],
        h1: ['bound_line', '= ', ' ='],
        h2: ['bound_line', '== ', ' =='],
        h3: ['bound_line', '=== ', ' ==='],
        h4: ['bound_line', '==== ', ' ===='],
        ordered: ['start_lines', ' 1.'],
        unordered: ['start_lines', ' *'],
        indent: ['start_lines', 'dont know'],
        hr: ['line_alone', '----'],
        table: ['line_alone', '|| A || B || C ||\n||   ||   ||   ||\n||   ||   ||   ||']
    }
}

