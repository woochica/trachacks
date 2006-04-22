inherits (template='tracmain.stan') [
    override (slot='pagebody') [
        div (id="container") [ 
            a (id="top"),
            p (_class="hide") [ 
                'Skip to: ',
                a (href="#menu") [ 'site menu' ],
                ' | ',
                a (href="#sectionmenu") [ 'section menu' ],
                ' | ',
                a (href="#main") [ 'main content' ],
            ],
            div (id="sitename") [
                h1 [ 'andreas06: falling leaves' ],
                span [ 'It is all about colors...' ],
                a (id="menu")
            ],
            div (id="nav") [
                ul [
                    li (id="current") [
                        a (href="index.html") [ 'Front page' ]
                    ],
                    li [
                        a (href="alternative.html") [ 'Alternative layout' ]
                    ],
                    li [
                        a (href="photo.html") [ 'Photo layout' ]
                    ],
                    li [
                        a (href="styles.html") [ 'Styles' ]
                    ],
                    li [
                        a (href="empty.html") [ 'Empty' ]
                    ],
                ],
                p (_class="hide") [
                    a (href="#top") ['Back to top']
                ]
            ],
            div (id="wrap1") [ 
                div (id="wrap2") [
                    div (id="topbox") [
                        strong [
                            span (_class="hide") [ 'Currently viewing: ' ],
                                a (href="index.html") [ 'andreas06: Falling leaves' ],
                                raquo,
                                a (href="index.html") [ 'Front page']
                        ]
                    ],
                    div (id="leftside") [
                        a (id="sectionmenu"),
                        p (_class="soft") [ 'Use the navigation tabs to read more about the'
                                           ' template and to see alternative layouts and features.' ],
                        h1 [ 'Example menu:' ],
                        p (_class="menublock") [ 
                            a (_class="nav", href="#") [ 'Downloads' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- MP3 files' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- MIDI tools' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- PDF Manuals' ],
                            br (_class="hide"),
                            a (_class="nav", href="#") [ 'Forum' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- Latest News' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- Members' ],
                            br (_class="hide"),
                            a (_class="nav sub", href="#") [ '- Newsletter' ],
                            br (_class="hide"),
                            a (_class="nav", href="#") [ 'Login' ],
                            br (_class="hide"),
                            a (_class="nav", href="#") [ 'Merchandise' ],
                            br (_class="hide"),
                            a (_class="hide", href="#top") [ 'Back to Top' ],
                        ]
                    ],
                    div (id="rightside") [
                        h1 [ 'Template info:' ],
                        p [ 'andreas06 is built with valid XHTML 1.1 and CSS2. It conforms'
                            ' to section 508 and a WCAG 1.0 AAA rating. It has full support'
                            ' for browser-based font-resizing, 100% readable also even in'
                            ' text-based browsers.' ],
                        p [ '/', strong [ 'Andreas' ] ],
                        h1 [ 'Links:' ],
                        p [ 
                            a (href="http://andreasviklund.com") [ 'My website' ],
                            br,
                            a (href="http://andreasviklund.com/templates") [ 'Free templates' ],
                            br,
                            a (href="http://baygroove.com") [ 'Baygroove.com' ],
                            br,
                            a (href="http://openwebdesign.org") [ 'Open Web Design' ],
                            br,
                            a (href="http://oswd.org") [ 'OSWD.org' ],
                            br,
                            a (href="http://www.solucija.com") [ 'sNews CMS' ],
                        ],
                        p (_class="smallcaps") [ 'andreas06 v1.2', br, '(Nov 28, 2005)' ],
                    ],
                    a (id="main"),
                    div (id="content") [
                        h1 [ 'Welcome to "falling leaves"...' ],
                        img (src="chrome/pyrus/img/gravatar-leaf.jpg", height="80",
                             width="80", alt="Gravatar example"),
                        p (_class="intro") [ '...also known as "andreas06", yet another open source '
                                            'template by Andreas. This one has a lot of useful features, '
                                            'such as the two-level menu and a good set of formatting and '
                                            'layout styles!' ],
                        p [ 'Like in my other templates, the extra features are all built into the '
                            'stylesheet. The simple structure of the code (all content is separated '
                            'from the presentation) makes it easy to customize the look and feel of '
                            'the design, and you get several layouts to choose from in the download '
                            'zip. Click the menu tabs to view the examples.' ],
                        p [ 'The design is inspired by the colors of the fall, since the template '
                            'was created as an entry in the ',
                            a (href="http://openwebdesign.org") [ 'Open Web Design' ],
                            '"fall/autumn" competition in October 2005 (where it as awarded 1st place).'
                            ' The colors are picked from a photo of the local park, taken on Oct 1st.' ],
                        h2 [ 'Open source design' ],
                        p [ 'This template is released as open source, which means that you are free '
                            'to use it in any way you may want to. If you like this design, you can '
                            'download my other designs directly from',
                            a (href="http://andreasviklund.com") [ 'my website'],
                            ' (where you can also find a WordPress version of this theme) or from Open '
                            'Web Design. Comments, questions and suggestions are always very welcome!' ],
                        p (_class="hide") [ 
                            a (href="#top") [ 'Back to top' ],
                        ],
                    ]
                ],
                div (id="footer") [ copy, 
                                    ' 2006 Pacopablo | Design by ',
                                    a (href="http://andreasviklund.com") [ 'Andreas Viklund' ],
                ]
            ]
        ]
    ]
]
