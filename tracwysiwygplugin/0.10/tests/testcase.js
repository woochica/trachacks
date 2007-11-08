addEvent(window, "load", function() {
    var unit = new TracWysiwyg.TestUnit();

    TracWysiwyg.tracBasePath = "./";
    var instance = new TracWysiwyg(unit.$("textarea"));
    var document = instance.contentDocument;

    function generate(dom, wikitext, withoutDomToWikitext, withoutWikitextToFragment) {
        dom = dom.cloneNode(true);
        var anonymous = dom.ownerDocument.createElement("div");
        anonymous.appendChild(dom);

        if (!withoutWikitextToFragment) {
            var fragment = instance.wikitextToFragment(wikitext, document);
            var generated = document.createElement("div");
            generated.appendChild(fragment);
            var generatedHtml = generated.innerHTML;
            if (!generated.addEventListener || window.opera) {
                generatedHtml = generatedHtml.replace(/\n\r/g, "\uffff").replace(/\uffff\n?/g, "\n");
            }
            this.assertEqual(anonymous.innerHTML, generatedHtml);
        }
        if (!withoutDomToWikitext) {
            this.assertEqual(wikitext, instance.domToWikitext(anonymous));
        }
    }

    function generateFragment(dom, wikitext) {
        generate.call(this, dom, wikitext, true);
    }

    function run() {
        var fragment = unit.fragment;
        var element = unit.element;

        unit.add("code block", function() {
            var dom = fragment(
                element("p", element("tt", "abc")),
                element("pre", { "class": "wiki" }, "{{{code-block"));
            var wikitext = [
                "`abc`",
                "",
                "{{{",
                "{{{code-block",
                "}}}" ].join("\n");
            generate.call(this, dom, wikitext);
        });
        unit.add("code block nest", function() {
            var dom = fragment(
                element("pre", { "class": "wiki" }, "#!python\n= level 1\n{{{\n= level 2\n}}}\n= level 1"));
            var wikitext = [
                "{{{",
                "#!python",
                "= level 1",
                "{{{",
                "= level 2",
                "}}}",
                "= level 1",
                "}}}" ].join("\n");
            generate.call(this, dom, wikitext);
        });

        unit.add("hr", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("hr"),
                element("ul",
                    element("li", "item 1"),
                    element("ol", element("li", "item 1.1"))),
                element("hr"));
            generateFragment.call(this, dom, [
                "Paragraph",
                "----",
                " * item 1",
                "   1. item 1.1",
                "----" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                "----",
                " * item 1",
                "   1. item 1.1",
                "",
                "----" ].join("\n"));
        });

        unit.add("bold italic", function() {
            var dom = element("p", element("b", element("i", "bold italic")));
            var wikitext = "'''''bold italic'''''";
            generate.call(this, dom, wikitext);
        });
        unit.add("bold", function() {
            var dom = element("p", element("b", "bold"));
            var wikitext = "'''bold'''";
            generate.call(this, dom, wikitext);
        });
        unit.add("italic", function() {
            var dom = element("p", element("i", "italic"));
            var wikitext = "''italic''";
            generate.call(this, dom, wikitext);
        });
        unit.add("underline", function() {
            var dom = element("p", element("u", "underline"));
            var wikitext = "__underline__";
            generate.call(this, dom, wikitext);
        });
        unit.add("strike-through", function() {
            var dom = element("p", element("del", "strike-through"));
            var wikitext = "~~strike-through~~";
            generate.call(this, dom, wikitext);
        });
        unit.add("superscript", function() {
            var dom = element("p", element("sup", "superscript"));
            var wikitext = "^superscript^";
            generate.call(this, dom, wikitext);
        });
        unit.add("subscript", function() {
            var dom = element("p", element("sub", "subscript"));
            var wikitext = ",,subscript,,";
            generate.call(this, dom, wikitext);
        });
        unit.add("monospace", function() {
            var dom = element("p", element("tt", "monospace"),
                ", ", element("tt", "mono`s`pace"),
                ", ", element("tt", "mono{{{s}}}pace"));
            var wikitext = "`monospace`, {{{mono`s`pace}}}, `mono{{{s}}}pace`";
            generate.call(this, dom, wikitext);
        });
        unit.add("italic -> bold", function() {
            var dom = element("p",
                "normal",
                element("i", "italic"),
                element("b", "bold"),
                "normal");
            var wikitext = "normal''italic'''''bold'''normal";
            generate.call(this, dom, wikitext);
        });
        unit.add("bold -> italic", function() {
            var dom = element("p",
                "normal",
                element("b", "bold"),
                element("i", "italic"),
                "normal");
            var wikitext = "normal'''bold'''''italic''normal";
            generate.call(this, dom, wikitext);
        });
        unit.add("[ italic [ xyz ] bold ]", function() {
            var dom = element("p",
                "normal",
                element("i", "italic", element("b", "xyz")),
                element("b", "bold"),
                "normal");
            var wikitext = "normal''italic'''xyz''bold'''normal";
            generate.call(this, dom, wikitext);
        });
        unit.add("overlapped markups", function() {
            var dom = element("p",
                "normal",
                element("b", "bold",
                    element("i", "italic",
                        element("u", "underline",
                            element("del", "strike-through",
                                element("sup", "superscript",
                                    element("sub", "subscript"))))),
                    element("u", element("del", element("sup", element("sub", "i")))),
                    element("del", element("sup", element("sub", "u"))),
                    element("sup", element("sub", "strike")),
                    element("sub", "sup"),
                    "sub"),
                ".");
            var wikitext = "normal'''bold''italic__underline~~strike-through^superscript,,subscript''i__u~~strike^sup,,sub'''.";
            generateFragment.call(this, dom, wikitext);
        });

        unit.add("! bold italic", function() {
            var dom = element("p", element("b", element("i", "bold''''' italic")), ".");
            var wikitext = "'''''bold!''''' italic'''''.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! bold", function() {
            var dom = element("p", element("b", "bold''' bold"), ".");
            var wikitext = "'''bold!''' bold'''.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! italic", function() {
            var dom = element("p", element("i", "italic'' italic"), ".");
            var wikitext = "''italic!'' italic''.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! underline", function() {
            var dom = element("p", element("u", "underline__ underline"), ".");
            var wikitext = "__underline!__ underline__.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! strike-through", function() {
            var dom = element("p", element("del", "strike~~through"), ".");
            var wikitext = "~~strike!~~through~~.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! superscript", function() {
            var dom = element("p", element("sup", "superscript^ superscript"), ".");
            var wikitext = "^superscript!^ superscript^.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! subscript", function() {
            var dom = element("p", element("sub", "subscript,, subscript"), ".");
            var wikitext = ",,subscript!,, subscript,,.";
            generate.call(this, dom, wikitext);
        });
        unit.add("! monospace", function() {
            var dom = element("p", "{{{monospace}}} or `monospace`");
            var wikitext = "!{{{monospace}}} or !`monospace`";
            generate.call(this, dom, wikitext);
        });

        unit.add("#ticket", function() {
            var dom = element("p",
                element("a", "#1234", {
                    href: "./search?q=ticket%3A1234", title: "ticket:1234",
                    "tracwysiwyg-link": "ticket:1234", onclick: "return false;" }),
                " #2345 &#3456");
            var wikitext = "#1234 !#2345 &#3456";
            generate.call(this, dom, wikitext);
        });

        unit.add("{report}", function() {
            var dom = element("p",
                "{987}",
                element("a", "{123}", {
                    href: "./search?q=report%3A123", title: "report:123",
                    "tracwysiwyg-link": "report:123", onclick: "return false;" }));
            var wikitext = "!{987}{123}";
            generate.call(this, dom, wikitext);
        });

        unit.add("[changeset]", function() {
            var dom = element("p",
                element("a", "[123]", {
                    href: "./search?q=changeset%3A123", title: "changeset:123",
                    "tracwysiwyg-link": "changeset:123", onclick: "return false;" }),
                ", ",
                element("a", "r234", {
                    href: "./search?q=changeset%3A234", title: "changeset:234",
                    "tracwysiwyg-link": "changeset:234", onclick: "return false;" }),
                ", ",
                element("a", "[345/trunk]", {
                    href: "./search?q=changeset%3A345%2Ftrunk", title: "changeset:345/trunk",
                    "tracwysiwyg-link": "changeset:345/trunk", onclick: "return false;" }),
                ", [123], r234, [345/trunk]");
            generateFragment.call(this, dom, "[123], r234, [345/trunk], ![123], !r234, ![345/trunk]");
            generate.call(this, dom, "[123], [changeset:234 r234], [345/trunk], ![123], !r234, ![345/trunk]");
        });

        unit.add("[log]", function() {
            var dom = element("p",
                "log - ",
                element("a", "r1:3", {
                    href: "./search?q=log%3A%401%3A3", title: "log:@1:3",
                    "tracwysiwyg-link": "log:@1:3", onclick: "return false;" }),
                ", r1:3, ",
                element("a", "[1:3]", {
                    href: "./search?q=log%3A%401%3A3", title: "log:@1:3",
                    "tracwysiwyg-link": "log:@1:3", onclick: "return false;" }),
                ", [1:3], ",
                element("a", "log:@1:3", {
                    href: "./search?q=log%3A%401%3A3", title: "log:@1:3",
                    "tracwysiwyg-link": "log:@1:3", onclick: "return false;" }),
                ", log:@1:3, ",
                element("a", "log:trunk@1:3", {
                    href: "./search?q=log%3Atrunk%401%3A3", title: "log:trunk@1:3",
                    "tracwysiwyg-link": "log:trunk@1:3", onclick: "return false;" }),
                ", log:trunk@1:3");
            generateFragment.call(this, dom, "log - r1:3, !r1:3, [1:3], ![1:3], log:@1:3, !log:@1:3, log:trunk@1:3, !log:trunk@1:3");
            generate.call(this, dom, "log - [log:@1:3 r1:3], !r1:3, [1:3], ![1:3], [log:@1:3 log:@1:3], !log:@1:3, [log:trunk@1:3 log:trunk@1:3], !log:trunk@1:3");
        });

        unit.add("wiki:TracLinks", function() {
            var dom = element("p",
                element("a", "link:WikiName", {
                    href: "./search?q=link%3AWikiName", title: "link:WikiName",
                    "tracwysiwyg-link": "link:WikiName", onclick: "return false;" }),
                " ",
                element("a", 'link:"Foo Bar"', {
                    href: "./search?q=link%3A%22Foo%20Bar%22", title: 'link:"Foo Bar"',
                    "tracwysiwyg-link": 'link:"Foo Bar"', onclick: "return false;" }),
                " ",
                element("a", 'link:"Foo Bar#baz"', {
                    href: "./search?q=link%3A%22Foo%20Bar%23baz%22", title: 'link:"Foo Bar#baz"',
                    "tracwysiwyg-link": 'link:"Foo Bar#baz"', onclick: "return false;" }),
                " ",
                element("a", "link:'Foo Bar'", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar'"),
                    title: "link:'Foo Bar'", "tracwysiwyg-link": "link:'Foo Bar'",
                    onclick: "return false;" }),
                " ",
                element("a", "link:'Foo Bar#baz'", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar#baz'"),
                    title: "link:'Foo Bar#baz'", "tracwysiwyg-link": "link:'Foo Bar#baz'",
                    onclick: "return false;" }),
                " ",
                element("a", "svn+ssh://example.com/trunk", {
                    href: "./search?q=" + encodeURIComponent("svn+ssh://example.com/trunk"),
                    title: "svn+ssh://example.com/trunk", "tracwysiwyg-link": "svn+ssh://example.com/trunk",
                    onclick: "return false;" }),
                " ",
                element("a", "repository", {
                    href: "./search?q=" + encodeURIComponent("svn+ssh://example.com/trunk"),
                    title: "svn+ssh://example.com/trunk", "tracwysiwyg-link": "svn+ssh://example.com/trunk",
                    onclick: "return false;" }),
                " ",
                element("a", "rfc-2396.compatible://link", {
                    href: "./search?q=" + encodeURIComponent("rfc-2396.compatible://link"),
                    title: "rfc-2396.compatible://link", "tracwysiwyg-link": "rfc-2396.compatible://link",
                    onclick: "return false;" }),
                " ",
                element("a", "RFC 2396", {
                    href: "./search?q=" + encodeURIComponent("rfc-2396.compatible://link"),
                    title: "rfc-2396.compatible://link", "tracwysiwyg-link": "rfc-2396.compatible://link",
                    onclick: "return false;" }),
                " link:'Foo Bar#baz'");
            generateFragment.call(this, dom, [
                "link:WikiName",
                'link:"Foo Bar" link:"Foo Bar#baz"',
                "link:'Foo Bar' link:'Foo Bar#baz'",
                "svn+ssh://example.com/trunk [svn+ssh://example.com/trunk repository]",
                "rfc-2396.compatible://link [rfc-2396.compatible://link RFC 2396]",
                "!link:'Foo Bar#baz'" ].join(" "));
            generate.call(this, dom, [
                "[link:WikiName link:WikiName]",
                '[link:"Foo Bar" link:"Foo Bar"] [link:"Foo Bar#baz" link:"Foo Bar#baz"]',
                "[link:'Foo Bar' link:'Foo Bar'] [link:'Foo Bar#baz' link:'Foo Bar#baz']",
                "[svn+ssh://example.com/trunk svn+ssh://example.com/trunk] [svn+ssh://example.com/trunk repository]",
                "[rfc-2396.compatible://link rfc-2396.compatible://link] [rfc-2396.compatible://link RFC 2396]",
                "!link:'Foo Bar#baz'" ].join(" "));
        });

        unit.add("[wiki:TracLinks label]", function() {
            var dom = element("p",
                element("a", "WikiName", {
                    href: "./search?q=link%3AWikiName", title: "link:WikiName",
                    "tracwysiwyg-link": "link:WikiName", onclick: "return false;" }),
                " ",
                element("a", "wiki name", {
                    href: "./search?q=link%3AWikiName", title: "link:WikiName",
                    "tracwysiwyg-link": "link:WikiName", onclick: "return false;" }),
                " ",
                element("a", "wiki]name", {
                    href: "./search?q=wiki%3AWikiName", title: "wiki:WikiName",
                    "tracwysiwyg-link": "wiki:WikiName", onclick: "return false;" }),
                " ",
                element("a", "wiki name", {
                    href: "./search?q=wiki%3AWikiName", title: "wiki:WikiName",
                    "tracwysiwyg-link": "wiki:WikiName", onclick: "return false;" }),
                " ",
                element("a", "Foo Bar", {
                    href: "./search?q=link%3A%22Foo%20Bar%22", title: 'link:"Foo Bar"',
                    "tracwysiwyg-link": 'link:"Foo Bar"', onclick: "return false;" }),
                " ",
                element("a", "Foo Bar#baz", {
                    href: "./search?q=link%3A%22Foo%20Bar%23baz%22", title: 'link:"Foo Bar#baz"',
                    "tracwysiwyg-link": 'link:"Foo Bar#baz"', onclick: "return false;" }),
                " ",
                element("a", "bar foo", {
                    href: "./search?q=link%3A%22Foo%20Bar%22", title: 'link:"Foo Bar"',
                    "tracwysiwyg-link": 'link:"Foo Bar"', onclick: "return false;" }),
                " ",
                element("a", 'foo "foobar" bar', {
                    href: "./search?q=link%3A%22Foo%20Bar%23baz%22", title: 'link:"Foo Bar#baz"',
                    "tracwysiwyg-link": 'link:"Foo Bar#baz"', onclick: "return false;" }),
                " ",
                element("a", "Foo Bar", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar'"),
                    title: "link:'Foo Bar'", "tracwysiwyg-link": "link:'Foo Bar'",
                    onclick: "return false;" }),
                " ",
                element("a", "Foo Bar#baz", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar#baz'"),
                    title: "link:'Foo Bar#baz'", "tracwysiwyg-link": "link:'Foo Bar#baz'",
                    onclick: "return false;" }),
                " ",
                element("a", "foo bar", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar'"),
                    title: "link:'Foo Bar'", "tracwysiwyg-link": "link:'Foo Bar'",
                    onclick: "return false;" }),
                " ",
                element("a", "foo 'foobar' bar", {
                    href: "./search?q=" + encodeURIComponent("link:'Foo Bar#baz'"),
                    title: "link:'Foo Bar#baz'",
                    "tracwysiwyg-link": "link:'Foo Bar#baz'",
                    onclick: "return false;" }),
                " [link:'Foo Bar#baz'] [link:'Foo Bar#baz' label]");
            generateFragment.call(this, dom, [
                "[link:WikiName]",
                "[link:WikiName 'wiki name']",
                '[wiki:WikiName "wiki]name"]',
                "[WikiName 'wiki name']",
                '[link:"Foo Bar"] [link:"Foo Bar#baz"]',
                '[link:"Foo Bar" "bar foo"] [link:"Foo Bar#baz" foo "foobar" bar]',
                "[link:'Foo Bar'] [link:'Foo Bar#baz']",
                "[link:'Foo Bar' 'foo bar'] [link:'Foo Bar#baz' foo 'foobar' bar]",
                "![link:'Foo Bar#baz'] ![link:'Foo Bar#baz' label]" ].join(" "));
            generate.call(this, dom, [
                "[link:WikiName]",
                "[link:WikiName wiki name]",
                '[wiki:WikiName "wiki]name"]',
                "[wiki:WikiName wiki name]",
                '[link:"Foo Bar" Foo Bar] [link:"Foo Bar#baz" Foo Bar#baz]',
                '[link:"Foo Bar" bar foo] [link:"Foo Bar#baz" foo "foobar" bar]',
                "[link:'Foo Bar' Foo Bar] [link:'Foo Bar#baz' Foo Bar#baz]",
                "[link:'Foo Bar' foo bar] [link:'Foo Bar#baz' foo 'foobar' bar]",
                "![link:'Foo Bar#baz'] ![link:'Foo Bar#baz' label]" ].join(" "));
        });

        unit.add("[/relative label]", function() {
            var dom = element("p",
                element("a", "Trac", {
                    href: "../trac", title: "../trac", "tracwysiwyg-link": "../trac",
                    onclick: "return false;" }),
                " ",
                element("a", "here", {
                    href: "/newticket?component=tracwysiwygplugin",
                    title: "/newticket?component=tracwysiwygplugin",
                    "tracwysiwyg-link": "/newticket?component=tracwysiwygplugin",
                    onclick: "return false;" }),
                " ",
                element("a", "host", {
                    href: "//hostname", title: "//hostname", "tracwysiwyg-link": "//hostname",
                    onclick: "return false;" }),
                " ",
                element("a", "images", {
                    href: "//hostname/images", title: "//hostname/images",
                    "tracwysiwyg-link": "//hostname/images", onclick: "return false;" }),
                " ",
                element("a", "anchor", {
                    href: "#anchor", title: "#anchor", "tracwysiwyg-link": "#anchor",
                    onclick: "return false;" }));
            var wikitext = [
                "[../trac Trac]",
                "[/newticket?component=tracwysiwygplugin here]",
                "[//hostname host]",
                "[//hostname/images images]",
                "[#anchor anchor]" ].join(" ");
            generate.call(this, dom, wikitext);
        });

        unit.add("[[macro]]", function() {
            var dom = element("p",
                "Line break ", element("br"), " another line", element("br"),
                "last line [[bR]] ![[Br]] [[Macro]] ![[Macro]]");
            generateFragment.call(this, dom, "Line break [[BR]] another line[[br]]last line ![[bR]] !![[Br]] [[Macro]] ![[Macro]]");
            generate.call(this, dom, "Line break [[BR]] another line[[BR]]last line ![[bR]] !![[Br]] [[Macro]] ![[Macro]]");
        });

        unit.add("WikiPageName", function() {
            var dom = element("p",
                element("a", "CamelCase", {
                    href: "./search?q=" + encodeURIComponent("wiki:CamelCase"),
                    title: "wiki:CamelCase", "tracwysiwyg-link": "wiki:CamelCase",
                    onclick: "return false;" }),
                " CamelCase FooBarA FOo FoobarA OneÅngström Oneångström");
            generateFragment.call(this, dom,
                "CamelCase !CamelCase FooBarA FOo FoobarA OneÅngström Oneångström");
            generate.call(this, dom,
                "[wiki:CamelCase] !CamelCase FooBarA FOo FoobarA OneÅngström Oneångström");
        });

        unit.add('["internal free link"]', function() {
            var dom = element("p",
                "link - ",
                element("a", "internal free link", {
                    href: "./search?q=" + encodeURIComponent('wiki:"internal free link"'),
                    title: 'wiki:"internal free link"', "tracwysiwyg-link": 'wiki:"internal free link"',
                    onclick: "return false;" }),
                ' - ["free link"]');
            generate.call(this, dom, 'link - [wiki:"internal free link" internal free link] - !["free link"]');
        });

        unit.add("citation", function() {
            var dom = fragment(
                element("blockquote", { "class": "citation" },
                    element("p", " This is the quoted text"),
                    element("blockquote", { "class": "citation" }, element("p", " a nested quote"))),
                element("p", "A comment on the above"),
                element("blockquote", { "class": "citation" },
                    element("blockquote", { "class": "citation" },
                        element("p", " start 2nd level")),
                    element("p", " first level")));
            generate.call(this, dom, [
                "> This is the quoted text",
                ">> a nested quote",
                "A comment on the above",
                "",
                ">> start 2nd level",
                "> first level" ].join("\n"));
        });

        unit.add("header", function() {
            var dom = fragment(
                element("h1", "Heading 1"),
                element("h2", { id: "anchor-2" }, "Heading 2"),
                element("h3", element("u", "Heading"), " ", element("i", "3")),
                element("h4", { id: "anchor-4" },
                    "Heading 4 with ",
                    element("a", "link", {
                        href: "./search?q=" + encodeURIComponent('wiki:WikiStart'),
                        title: 'wiki:WikiStart', "tracwysiwyg-link": 'wiki:WikiStart',
                        onclick: "return false;" })),
                element("h5", "Heading 5"),
                element("h6", { id: "anchor-6" }, "Heading 6"));
            generate.call(this, dom, [
                "= Heading 1 =",
                "== Heading 2 == #anchor-2",
                "=== __Heading__ ''3'' ===",
                "==== Heading 4 with [wiki:WikiStart link] ==== #anchor-4",
                "===== Heading 5 =====",
                "====== Heading 6 ====== #anchor-6" ].join("\n"));
        });

        unit.add("list", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("ul",
                    element("li", "foo bar boo baz"),
                    element("ul", element("li", "Subitem Subitem line 2")),
                    element("li", "item 2 item 2 line 2")),
                element("p", "Paragraph"));
            generateFragment.call(this, dom, [
                "Paragraph",
                " * foo bar",
                "   boo baz",
                "   * Subitem",
                "     Subitem line 2",
                " * item 2",
                "   item 2 line 2",
                "Paragraph" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                " * foo bar boo baz",
                "   * Subitem Subitem line 2",
                " * item 2 item 2 line 2",
                "",
                "Paragraph" ].join("\n"));
        });

        unit.add("list 2", function() {
            var dom = fragment(
                element("ul",
                    element("li", "foo bar boo baz"),
                    element("ul",
                        element("li", "Subitem 1"),
                        element("ul",
                            element("li", "nested item 1"),
                            element("li", "nested item 2 nested item 2 continued")),
                        element("li", "Subitem 2 subitem 2 continued"),
                        element("li", "Subitem 3 subitem 3 continued")),
                    element("li", "item 2 item 2 line 2")),
                element("p", "Paragraph"));
            generateFragment.call(this, dom, [
                "    * foo bar",
                "      boo baz",
                "           * Subitem 1",
                "             - nested item 1",
                "             - nested item 2",
                "             nested item 2 continued",
                "            * Subitem 2",
                "             subitem 2 continued",
                "            * Subitem 3",
                "            subitem 3 continued",
                "    * item 2",
                "     item 2 line 2",
                "Paragraph" ].join("\n"));
            generate.call(this, dom, [
                " * foo bar boo baz",
                "   * Subitem 1",
                "     * nested item 1",
                "     * nested item 2 nested item 2 continued",
                "   * Subitem 2 subitem 2 continued",
                "   * Subitem 3 subitem 3 continued",
                " * item 2 item 2 line 2",
                "",
                "Paragraph" ].join("\n"));
        });

        unit.add("ordered list", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("ol",
                    element("li", "item 1"),
                    element("ol", { "class": "arabiczero" },
                        element("li", "item 1.1"),
                        element("li", "item 1.2"),
                        element("ol", { "class": "loweralpha" },
                            element("li", "item 1.2.a"),
                            element("li", "item 1.2.b")),
                        element("li", "item 1.3"),
                        element("ol", { "class": "loweralpha" },
                            element("li", "item 1.3.a"),
                            element("li", "item 1.3.b")),
                        element("li", "item 1.4"),
                        element("ol", { "class": "upperalpha" },
                            element("li", "item 1.4.A"),
                            element("li", "item 1.4.B"),
                            element("li", "item 1.4.C")),
                        element("li", "item 1.5"),
                        element("ol", { "class": "upperalpha" },
                            element("li", "item 1.5.A")),
                        element("li", "item 1.6"),
                        element("ol", { "class": "lowerroman" },
                            element("li", "item 1.6.i"),
                            element("li", "item 1.6.ii")),
                        element("li", "item 1.7"),
                        element("ol", { "class": "upperroman" },
                            element("li", "item 1.7.I"),
                            element("li", "item 1.7.II")))),
                element("p", "Paragraph"));
            generateFragment.call(this, dom, [
                "Paragraph",
                " 1. item 1",
                "   0. item 1.1",
                "   2. item 1.2",
                "     a. item 1.2.a",
                "     z. item 1.2.b",
                "   a. item 1.3",
                "     b. item 1.3.a",
                "     y. item 1.3.b",
                "   Z. item 1.4",
                "     A. item 1.4.A",
                "     z. item 1.4.B",
                "     z. item 1.4.C",
                "   ii. item 1.5",
                "     C. item 1.5.A",
                "   XVI. item 1.6",
                "     i. item 1.6.i",
                "     x. item 1.6.ii",
                "   0. item 1.7",
                "     I. item 1.7.I",
                "     III. item 1.7.II",
                "Paragraph" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                " 1. item 1",
                "   0. item 1.1",
                "   0. item 1.2",
                "     a. item 1.2.a",
                "     a. item 1.2.b",
                "   0. item 1.3",
                "     a. item 1.3.a",
                "     a. item 1.3.b",
                "   0. item 1.4",
                "     A. item 1.4.A",
                "     A. item 1.4.B",
                "     A. item 1.4.C",
                "   0. item 1.5",
                "     A. item 1.5.A",
                "   0. item 1.6",
                "     i. item 1.6.i",
                "     i. item 1.6.ii",
                "   0. item 1.7",
                "     I. item 1.7.I",
                "     I. item 1.7.II",
                "",
                "Paragraph" ].join("\n"));
        });

        unit.add("list + ordered list", function() {
            var dom = fragment(
                element("ul",
                    element("li", "Item 1"),
                    element("ul", element("li", "Item 1.1")),
                    element("li", "Item 2")),
                element("ol",
                    element("li", "Item 1"),
                    element("ol", { "class": "loweralpha" },
                        element("li", "Item 1.a"),
                        element("li", "Item 1.b"),
                        element("ol", { "class": "lowerroman" },
                            element("li", "Item 1.b.i"),
                            element("li", "Item 1.b.ii"))),
                    element("li", "Item 2")),
                element("p", "And numbered lists can also be given an explicit number:"),
                element("ol", { start: 3 }, element("li", "Item 3")));
            generateFragment.call(this, dom, [
                " * Item 1",
                "   * Item 1.1",
                " * Item 2",
                " 1. Item 1",
                "   a. Item 1.a",
                "   a. Item 1.b",
                "      i. Item 1.b.i",
                "      i. Item 1.b.ii",
                " 1. Item 2",
                "And numbered lists can also be given an explicit number:",
                " 3. Item 3" ].join("\n"));
            generate.call(this, dom, [
                " * Item 1",
                "   * Item 1.1",
                " * Item 2",
                "",
                " 1. Item 1",
                "   a. Item 1.a",
                "   a. Item 1.b",
                "     i. Item 1.b.i",
                "     i. Item 1.b.ii",
                " 1. Item 2",
                "",
                "And numbered lists can also be given an explicit number:",
                "",
                " 3. Item 3" ].join("\n"));
        });

        unit.add("list + code block", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("ul",
                    element("li",
                        "item 1",
                        element("pre", { "class": "wiki" }, "code")),
                    element("ul",
                        element("li",
                            "item 1.1",
                            element("pre", { "class": "wiki" }, "code"),
                            " cont.",
                            element("pre", { "class": "wiki" }, "code"))),
                    element("li",
                        "item 2",
                        element("pre", { "class": "wiki" }, "code"))),
                element("ol", element("li", "item 1")));
            generateFragment.call(this, dom, [
                "Paragraph",
                " * item 1",
                "{{{",
                "code",
                "}}}",
                "   * item 1.1",
                "{{{",
                "code",
                "}}}",
                "     cont.",
                "{{{",
                "code",
                "}}}",
                " * item 2",
                "{{{",
                "code",
                "}}}",
                " 1. item 1" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                " * item 1",
                "{{{",
                "code",
                "}}}",
                "   * item 1.1",
                "{{{",
                "code",
                "}}}",
                "     cont.",
                "{{{",
                "code",
                "}}}",
                " * item 2",
                "{{{",
                "code",
                "}}}",
                "",
                " 1. item 1" ].join("\n"));
        });

        unit.add("definition", function() {
            var dom = element("dl",
                element("dt", "python"),
                element("dd", "www.python.org :: cont."),
                element("dt", element("b", "trac")),
                element("dd",
                    element("b", "trac"), ".edgewall.org cont.",
                    " ", element("tt", "trac-hacks::"), " trac-hacks.org"));
            generateFragment.call(this, dom, [
                " python:: www.python.org :: cont.",
                " '''trac''':: '''trac'''.edgewall.org",
                "   cont.",
                " `trac-hacks::` trac-hacks.org" ].join("\n"));
            generate.call(this, dom, [
                " python:: www.python.org :: cont.",
                " '''trac''':: '''trac'''.edgewall.org cont. `trac-hacks::` trac-hacks.org" ].join("\n"));
        });

        unit.add("blockquote", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("blockquote",
                    element("p", "blockquote 1 cont. 1"),
                    element("blockquote",
                        element("p", "blockquote 1.1"),
                        element("blockquote", element("p", "blockquote 1.1.1 cont. 1.1.1")),
                        element("p", "blockquote 1.2")),
                    element("p", "blockquote 2")),
                element("p", "Paragraph"));
            generateFragment.call(this, dom, [
                "Paragraph",
                "  blockquote 1",
                "  cont. 1",
                "    blockquote 1.1",
                "      blockquote 1.1.1",
                "      cont. 1.1.1",
                "     blockquote 1.2",
                "    blockquote 2",
                "Paragraph" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                "  blockquote 1 cont. 1",
                "    blockquote 1.1",
                "      blockquote 1.1.1 cont. 1.1.1",
                "    blockquote 1.2",
                "  blockquote 2",
                "Paragraph" ].join("\n"));
        });

        unit.add("table", function() {
            var dom = fragment(
                element("p", "Paragraph"),
                element("table", { "class": "wiki" },
                    element("tbody",
                        element("tr", element("td", "1.1"), element("td", "1.2")),
                        element("tr", element("td", "2.1")),
                        element("tr",
                            element("td", "3.1"),
                            element("td", element("u", "3.2")),
                            element("td", element("tt", "3.3"))))),
                element("p", "Paragraph"));
            generateFragment.call(this, dom, [
                "Paragraph",
                "||1.1||1.2||",
                "||2.1",
                "||3.1||__3.2__||`3.3`",
                "Paragraph" ].join("\n"));
            generate.call(this, dom, [
                "Paragraph",
                "",
                "||1.1||1.2||",
                "||2.1||",
                "||3.1||__3.2__||`3.3`||",
                "",
                "Paragraph" ].join("\n"));
        });

        unit.run();
    }

    setTimeout(run, 1000);
});
