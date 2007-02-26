(function() {
    var media_wiki_init = function() {
        var divs = document.getElementsByTagName('div');
        var wikiwyg_divs = [];
        for (var i = 0; i < divs.length; i++) {
            var div = divs[i];
            if (! div.id.match(/^wikiwyg_section_\d+$/)) continue;
            wikiwyg_divs.push(div);
        }
        for (var i = 0; i < wikiwyg_divs.length; i++) {
            var div = wikiwyg_divs[i];
            var section_number = div.id.replace(/.*?(\d+)$/, '$1');
            var success = Wikiwyg.MediaWiki.setup_wikiwyg_section(
                div, section_number
            );
            if (! success) return;
        }
    }
    if (window.addEventListener)
        window.addEventListener("load", media_wiki_init, false);
    else if (window.attachEvent)
        window.attachEvent("onload", media_wiki_init);
})();

//------------------------------------------------------------------------------
proto = new Subclass('Wikiwyg.MediaWiki', 'Wikiwyg');
klass = Wikiwyg.MediaWiki;

klass.setup_wikiwyg_section = function(section_div, section_number) {
    var myConfig = {
        doubleClickToEdit: true,
        toolbarClass: 'Wikiwyg.Toolbar.MediaWiki',
        toolbar: {
            imagesLocation: '/wikiwyg/demo/wikipedia/images/'
        },
        wysiwyg: {
            iframeId: 'wikiwyg_iframe_' + section_number
        }
    }
    var myWikiwyg = new Wikiwyg.MediaWiki();
    myWikiwyg.createWikiwygArea(section_div, myConfig);
    if (! myWikiwyg.enabled) return false;
    var edit_button_span =
        document.getElementById('wikiwyg_edit_' + section_number);
    var edit_button = edit_button_span.getElementsByTagName('a')[0];
    edit_button.onclick = function() {
        myWikiwyg.editMode();
        return false;
    }
    myWikiwyg.section_number = section_number;
    return true;
}

proto.modeClasses = [
    'Wikiwyg.Wysiwyg',
    'Wikiwyg.Wikitext.MediaWiki',
    'Wikiwyg.Preview'
];
proto.submit_action_form = function(action, value) {
    var form = document.createElement('form');
    form.setAttribute('action', action);
    form.setAttribute('method', 'POST');
    for (var name in value) {
        var input = document.createElement('input');
        input.setAttribute('type', 'hidden');
        input.setAttribute('name', name);
        input.setAttribute('value', value[name])
        form.appendChild(input);
    }
    var div = this.div;
    div.parentNode.insertBefore(form, div);
    form.submit();
}

proto.getEdittime = function(title, section) {
    var url = 'index.php?page_title=' + title +
	      '&action=edit&section=' + section;
    var html = Ajax.get(url);
    var div = document.createElement('div');
    div.innerHTML = html;
    return div.getElementsByTagName("form")[0].elements.wpEdittime.value
}

proto.saveChanges = function() {
    var page_title = String(window.location).replace(/.*\//, '').replace(/.*title=/, '').replace(/;.*/, '');

    wpEdittime = this.getEdittime(page_title, this.section_number); 

    var self = this;
    var submit_changes = function(wikitext) {
        self.submit_action_form(
	    '/index.php',
            {
	    'title': page_title,
	    'action': "submit",
	    'wpSection': self.section_number,
	    'wpTextbox1': wikitext,
	    'wpEdittime':  wpEdittime,
	    'wpSave': "Save page"
	    }
        );
    }
    var self = this;
    if (this.current_mode.classname.match(/(Wysiwyg|Preview)/)) {
        this.current_mode.toHtml(
            function(html) {
                var wikitext_mode = self.mode_objects['Wikiwyg.Wikitext.MediaWiki'];
                wikitext_mode.convertHtmlToWikitext(
                    html,
                    function(wikitext) { submit_changes(wikitext) }
                );
            }
        );
    }
    else {
        submit_changes(this.current_mode.toWikitext());
    }
}

//------------------------------------------------------------------------------
proto = new Subclass('Wikiwyg.Toolbar.MediaWiki', 'Wikiwyg.Toolbar');

proto.config = {
    divId: null,
    imagesLocation: 'images/',
    imagesExtension: '.png',
    controlLayout: [
        'save', 'cancel', 'mode_selector', '/',
        'bold', 'italic',
        'link',
        'h2',
	'hr'
    ],
    controlLabels: {
        save: 'Save',
        cancel: 'Cancel',
        bold: 'Bold (Ctrl+b)',
        italic: 'Italic (Ctrl+i)',
        hr: 'Horizontal Rule',
        ordered: 'Numbered List',
        unordered: 'Bulleted List',
        indent: 'More Indented',
        outdent: 'Less Indented',
        label: '[Style]',
        p: 'Normal Text',
        pre: 'Preformatted',
        h1: 'Heading 1',
        h2: 'Heading 2',
        h3: 'Heading 3',
        h4: 'Heading 4',
        link: 'Create Link',
        table: 'Create Table'
    }
};

//------------------------------------------------------------------------------
proto = new Subclass('Wikiwyg.Wikitext.MediaWiki', 'Wikiwyg.Wikitext');

proto.convertWikitextToHtml = function(wikitext, func) {
  var query = "text=" + encodeURIComponent(wikitext);
  Wikiwyg.liveUpdate('POST',
		      '/index.php/Special:EZParser',
		      query,
		      func
		      );
}

proto.config = {
    textareaId: null,
    supportCamelCaseLinks: false,
    javascriptLocation: null,
    clearRegex: null,
    editHeightMinimum: 10,
    editHeightAdjustment: 1.3,
    markupRules: {
        link: ['bound_phrase', '[[', ']]'],
        bold: ['bound_phrase', "'''", "'''"],
        italic: ['bound_phrase', "''", "''"],
        p: ['start_lines', ''],
        pre: ['start_lines', '    '],
        h1: ['bound_line', '= ', ' ='],
        h2: ['bound_line', '== ', ' =='],
        h3: ['bound_line', '=== ', ' ==='],
        h4: ['bound_line', '==== ', ' ===='],
        ordered: ['start_lines', '#'],
        unordered: ['start_lines', '*'],
        indent: ['start_lines', '>'],
        hr: ['line_alone', '----'],
        table: ['line_alone', '| A | B | C |\n|   |   |   |\n|   |   |   |']
    }
}

//------------------------------------------------------------------------------
// Ajax support
//------------------------------------------------------------------------------
if (! this.Ajax) Ajax = {};

Ajax.get = function(url, callback) {
    var req = new XMLHttpRequest();
    req.open('GET', url, Boolean(callback));
    return Ajax._send(req, null, callback);
}

Ajax.post = function(url, data, callback) {
    var req = new XMLHttpRequest();
    req.open('POST', url, Boolean(callback));
    req.setRequestHeader(
        'Content-Type', 
        'application/x-www-form-urlencoded'
    );
    return Ajax._send(req, data, callback);
}

Ajax._send = function(req, data, callback) {
    if (callback) {
        req.onreadystatechange = function() {
            if (req.readyState == 4) {
                if(req.status == 200)
                    callback(req.responseText);
            }
        };
    }
    req.send(data);
    if (!callback) {
        if (req.status != 200)
            throw('Request for "' + url +
                  '" failed with status: ' + req.status);
        return req.responseText;
    }
}

//------------------------------------------------------------------------------
// Cross-Browser XMLHttpRequest v1.1
//------------------------------------------------------------------------------
/*
Emulate Gecko 'XMLHttpRequest()' functionality in IE and Opera. Opera requires
the Sun Java Runtime Environment <http://www.java.com/>.

by Andrew Gregory
http://www.scss.com.au/family/andrew/webdesign/xmlhttprequest/

This work is licensed under the Creative Commons Attribution License. To view a
copy of this license, visit http://creativecommons.org/licenses/by/1.0/ or send
a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305,
USA.
*/

// IE support
if (window.ActiveXObject && !window.XMLHttpRequest) {
  window.XMLHttpRequest = function() {
    return new ActiveXObject((navigator.userAgent.toLowerCase().indexOf('msie 5') != -1) ? 'Microsoft.XMLHTTP' : 'Msxml2.XMLHTTP');
  };
}

// Opera support
if (window.opera && !window.XMLHttpRequest) {
  window.XMLHttpRequest = function() {
    this.readyState = 0; // 0=uninitialized,1=loading,2=loaded,3=interactive,4=complete
    this.status = 0; // HTTP status codes
    this.statusText = '';
    this._headers = [];
    this._aborted = false;
    this._async = true;
    this.abort = function() {
      this._aborted = true;
    };
    this.getAllResponseHeaders = function() {
      return this.getAllResponseHeader('*');
    };
    this.getAllResponseHeader = function(header) {
      var ret = '';
      for (var i = 0; i < this._headers.length; i++) {
        if (header == '*' || this._headers[i].h == header) {
          ret += this._headers[i].h + ': ' + this._headers[i].v + '\n';
        }
      }
      return ret;
    };
    this.setRequestHeader = function(header, value) {
      this._headers[this._headers.length] = {h:header, v:value};
    };
    this.open = function(method, url, async, user, password) {
      this.method = method;
      this.url = url;
      this._async = true;
      this._aborted = false;
      if (arguments.length >= 3) {
        this._async = async;
      }
      if (arguments.length > 3) {
        // user/password support requires a custom Authenticator class
        opera.postError('XMLHttpRequest.open() - user/password not supported');
      }
      this._headers = [];
      this.readyState = 1;
      if (this.onreadystatechange) {
        this.onreadystatechange();
      }
    };
    this.send = function(data) {
      if (!navigator.javaEnabled()) {
        alert("XMLHttpRequest.send() - Java must be installed and enabled.");
        return;
      }
      if (this._async) {
        setTimeout(this._sendasync, 0, this, data);
        // this is not really asynchronous and won't execute until the current
        // execution context ends
      } else {
        this._sendsync(data);
      }
    }
    this._sendasync = function(req, data) {
      if (!req._aborted) {
        req._sendsync(data);
      }
    };
    this._sendsync = function(data) {
      this.readyState = 2;
      if (this.onreadystatechange) {
        this.onreadystatechange();
      }
      // open connection
      var url = new java.net.URL(new java.net.URL(window.location.href), this.url);
      var conn = url.openConnection();
      for (var i = 0; i < this._headers.length; i++) {
        conn.setRequestProperty(this._headers[i].h, this._headers[i].v);
      }
      this._headers = [];
      if (this.method == 'POST') {
        // POST data
        conn.setDoOutput(true);
        var wr = new java.io.OutputStreamWriter(conn.getOutputStream());
        wr.write(data);
        wr.flush();
        wr.close();
      }
      // read response headers
      // NOTE: the getHeaderField() methods always return nulls for me :(
      var gotContentEncoding = false;
      var gotContentLength = false;
      var gotContentType = false;
      var gotDate = false;
      var gotExpiration = false;
      var gotLastModified = false;
      for (var i = 0; ; i++) {
        var hdrName = conn.getHeaderFieldKey(i);
        var hdrValue = conn.getHeaderField(i);
        if (hdrName == null && hdrValue == null) {
          break;
        }
        if (hdrName != null) {
          this._headers[this._headers.length] = {h:hdrName, v:hdrValue};
          switch (hdrName.toLowerCase()) {
            case 'content-encoding': gotContentEncoding = true; break;
            case 'content-length'  : gotContentLength   = true; break;
            case 'content-type'    : gotContentType     = true; break;
            case 'date'            : gotDate            = true; break;
            case 'expires'         : gotExpiration      = true; break;
            case 'last-modified'   : gotLastModified    = true; break;
          }
        }
      }
      // try to fill in any missing header information
      var val;
      val = conn.getContentEncoding();
      if (val != null && !gotContentEncoding) this._headers[this._headers.length] = {h:'Content-encoding', v:val};
      val = conn.getContentLength();
      if (val != -1 && !gotContentLength) this._headers[this._headers.length] = {h:'Content-length', v:val};
      val = conn.getContentType();
      if (val != null && !gotContentType) this._headers[this._headers.length] = {h:'Content-type', v:val};
      val = conn.getDate();
      if (val != 0 && !gotDate) this._headers[this._headers.length] = {h:'Date', v:(new Date(val)).toUTCString()};
      val = conn.getExpiration();
      if (val != 0 && !gotExpiration) this._headers[this._headers.length] = {h:'Expires', v:(new Date(val)).toUTCString()};
      val = conn.getLastModified();
      if (val != 0 && !gotLastModified) this._headers[this._headers.length] = {h:'Last-modified', v:(new Date(val)).toUTCString()};
      // read response data
      var reqdata = '';
      var stream = conn.getInputStream();
      if (stream) {
        var reader = new java.io.BufferedReader(new java.io.InputStreamReader(stream));
        var line;
        while ((line = reader.readLine()) != null) {
          if (this.readyState == 2) {
            this.readyState = 3;
            if (this.onreadystatechange) {
              this.onreadystatechange();
            }
          }
          reqdata += line + '\n';
        }
        reader.close();
        this.status = 200;
        this.statusText = 'OK';
        this.responseText = reqdata;
        this.readyState = 4;
        if (this.onreadystatechange) {
          this.onreadystatechange();
        }
        if (this.onload) {
          this.onload();
        }
      } else {
        // error
        this.status = 404;
        this.statusText = 'Not Found';
        this.responseText = '';
        this.readyState = 4;
        if (this.onreadystatechange) {
          this.onreadystatechange();
        }
        if (this.onerror) {
          this.onerror();
        }
      }
    };
  };
}
// ActiveXObject emulation
if (!window.ActiveXObject && window.XMLHttpRequest) {
  window.ActiveXObject = function(type) {
    switch (type.toLowerCase()) {
      case 'microsoft.xmlhttp':
      case 'msxml2.xmlhttp':
        return new XMLHttpRequest();
    }
    return null;
  };
}


//------------------------------------------------------------------------------
// JSON Support
//------------------------------------------------------------------------------

/*
Copyright (c) 2005 JSON.org
*/
var JSON = function () {
    var m = {
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        s = {
            'boolean': function (x) {
                return String(x);
            },
            number: function (x) {
                return isFinite(x) ? String(x) : 'null';
            },
            string: function (x) {
                if (/["\\\x00-\x1f]/.test(x)) {
                    x = x.replace(/([\x00-\x1f\\"])/g, function(a, b) {
                        var c = m[b];
                        if (c) {
                            return c;
                        }
                        c = b.charCodeAt();
                        return '\\u00' +
                            Math.floor(c / 16).toString(16) +
                            (c % 16).toString(16);
                    });
                }
                return '"' + x + '"';
            },
            object: function (x) {
                if (x) {
                    var a = [], b, f, i, l, v;
                    if (x instanceof Array) {
                        a[0] = '[';
                        l = x.length;
                        for (i = 0; i < l; i += 1) {
                            v = x[i];
                            f = s[typeof v];
                            if (f) {
                                v = f(v);
                                if (typeof v == 'string') {
                                    if (b) {
                                        a[a.length] = ',';
                                    }
                                    a[a.length] = v;
                                    b = true;
                                }
                            }
                        }
                        a[a.length] = ']';
                    } else if (x instanceof Object) {
                        a[0] = '{';
                        for (i in x) {
                            v = x[i];
                            f = s[typeof v];
                            if (f) {
                                v = f(v);
                                if (typeof v == 'string') {
                                    if (b) {
                                        a[a.length] = ',';
                                    }
                                    a.push(s.string(i), ':', v);
                                    b = true;
                                }
                            }
                        }
                        a[a.length] = '}';
                    } else {
                        return;
                    }
                    return a.join('');
                }
                return 'null';
            }
        };
    return {
        copyright: '(c)2005 JSON.org',
        license: 'http://www.crockford.com/JSON/license.html',
        stringify: function (v) {
            var f = s[typeof v];
            if (f) {
                v = f(v);
                if (typeof v == 'string') {
                    return v;
                }
            }
            return null;
        },
        parse: function (text) {
            try {
                return !(/[^,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]/.test(
                        text.replace(/"(\\.|[^"\\])*"/g, ''))) &&
                    eval('(' + text + ')');
            } catch (e) {
                return false;
            }
        }
    };
}();
