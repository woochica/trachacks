TracWysiwyg.TestUnit = function() {
    this.cases = {};
    this.assertCount = 0;
};

(function() {
    var prototype = TracWysiwyg.TestUnit.prototype;

    prototype.inspect = function(value) {
        var type = typeof value;
        switch (type) {
        case "string":
            return value.replace(/[\u0000-\u001f\u007f\ufffe\uffff]/g, function(m) {
                var code = m.charCodeAt(0);
                switch (code) {
                case 9:  return "\\t";
                case 10: return "\\n";
                case 11: return "\\v";
                case 12: return "\\f";
                case 13: return "\\r";
                }
                return "\\" + (0x10000 + code).toString(16).substring(1);
            });
            break;
        default:
            return "{%}".replace("%", type) + value.toString();
        }
    };

    prototype.fragment = function() {
        var fragment = document.createDocumentFragment();
        var length = arguments.length;
        for (var i = 0; i < length; i++) {
            fragment.appendChild(arguments[i]);
        }
        return fragment;
    };

    prototype.element = function(tag) {
        var d = document;
        var element = d.createElement(tag);
        for (var i = 1; i < arguments.length; i++) {
            var arg = arguments[i];
            switch (typeof arg) {
            case "object":
                if (typeof arg.nodeType == "undefined") {
                    for (var name in arg) {
                        var value = arg[name];
                        switch (name) {
                        case "id":
                            element.id = value;
                            break;
                        case "class": case "className":
                            element.className = value;
                            break;
                        default:
                            element.setAttribute(name, value);
                            break;
                        }
                    }
                    continue;
                }
                break;
            case "string":
                arg = d.createTextNode(arg);
                break;
            }
            element.appendChild(arg);
        }
        return element;
    };

    prototype.text = function(text) {
        return document.createTextNode(text);
    };

    prototype.$ = function(id) {
        return typeof id == "string" ? document.getElementById(id) : id;
    };

    prototype.add = function(name, method) {
        if (name in this.cases) {
            throw "'" + name + "' is in use.";
        }
        this.cases[name] = method;
    };

    prototype.assertEqual = function(expected, actual, label) {
        this.assertCount++;
        if (typeof (expected) == typeof (actual) && expected == actual) {
            return true;
        }
        throw (label || "") + "[@]\n".replace(/@/g, this.assertCount)
            + this.inspect(expected) + " (" + expected.length + ")\n"
            + this.inspect(actual) + " (" + actual.length + ")";
    };

    prototype.run = function() {
        var self = this
        var $ = this.$, element = this.element, text = this.text;
        var d = document;
        var cases = this.cases;
        var names = [];
        for (var name in cases) {
            names.push(name);
        }

        var container = $("testunit");
        var count;
        if (container) {
            container.parentNode.removeChild(container);
        }
        container = element(
            "table", { id: "testunit" },
            element("caption", { id: "testunit.summary" }),
            element("tbody", { id: "testunit.body" }));
        d.body.appendChild(container);
        var body = $("testunit.body");
        var summary = $("testunit.summary");
        for (count = 0; count < names.length; count++) {
            body.appendChild(
                element("tr",
                    element("td", names[count]),
                    element("td", { id: "testcase." + count }, "...")));
        }

        this.assertCount = 0;
        count = 0;
        var success = 0;
        var invoke = function() {
            if (count >= names.length) {
                return;
            }

            var cell = $("testcase." + count);
            cell.className = "current";
            try {
                cases[names[count]].call(self);
                cell.className = "success";
                cell.replaceChild(text("OK"), cell.firstChild);
                success++;
            }
            catch (e) {
                cell.className = "failure";
                var message = e.message || e.toString();
                if (e.stack) {
                    message = [ message, e.stack ].join("\n\n");
                }
                cell.replaceChild(
                    element("textarea", { id: "testcase." + count + ".textarea", rows: message.split("\n").length, cols: 80 }),
                    cell.firstChild);
                $("testcase." + count + ".textarea").value = message;
            }
            summary.innerHTML = success + " / " + names.length;

            count++;
            setTimeout(invoke, 10);
        };

        invoke();
    };
})();
